# -*- coding: utf-8 -*-
"""
reproduce_masumi_yamada_2014.py
=============================================================================
專業地震資料分析腳本：完整復刻 Masumi Yamada 簡報中 2014 高雄氣爆波形分析圖表

核心設定：
  - 氣爆中心座標：(22.6120N, 120.3188E)（前鎮區光華/二聖路口）
  - 時間原點 (t0)：2014-07-31T13:00:00.000000Z
  - 氣爆主震波視窗：t = 10500 至 10800 秒（約 15:55 至 16:00 UTC）
  - 頻率帶通濾波：2.0 - 8.0 Hz (4th order Butterworth, zerophase)
  - 產出四大圖表（300 DPI）：
    1. 01_record_section_distance.png
    2. 02_original_vs_bp2-8Hz.png
    3. 03_near_field_3components.png
    4. 04_spectrogram_kau.png
=============================================================================
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import glob
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy import signal
import obspy
from obspy import UTCDateTime
from obspy.geodetics import gps2dist_azimuth

# 設置中文字體與負號支援
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. 核心參數與座標設定
# ==========================================
EPICENTER = (22.6120, 120.3188) # (緯度 N, 經度 E)
T0 = UTCDateTime('2014-07-31T13:00:00.000000Z')

STATION_COORDS = {
    'KAU': (22.566, 120.315),
    'SGL': (22.613, 120.408),
    'WLC': (22.754, 120.375),
    'SSD': (22.728, 120.648),
    'SNJ': (22.825, 120.389),
    'SCS': (22.955, 120.407),
    'SCZ': (23.003, 120.579),
    'TAI1': (22.997, 120.208),
    'SGS': (23.116, 120.627),
    'TTN': (22.752, 121.155)
}

# ==========================================
# 2. 自動搜尋與載入 MiniSEED 檔案
# ==========================================
def find_and_load_mseed_files(search_dir='.'):
    """
    遞迴搜尋目錄中的 MiniSEED 檔案（.mseed, .miniseed 或無副檔名 GDMS 檔），
    並讀入 ObsPy Stream。
    """
    print('=' * 65)
    print(f'正在搜尋目錄: {os.path.abspath(search_dir)}')
    print('=' * 65)
    
    candidate_files = []
    for root, _, files in os.walk(search_dir):
        for f in files:
            p = os.path.join(root, f)
            # 排除生成的 png 圖表與 python 腳本
            if f.endswith(('.png', '.py', '.pdf', '.log')):
                continue
            candidate_files.append(p)

    st_raw = obspy.Stream()
    loaded_files = []

    for fpath in candidate_files:
        try:
            temp_st = obspy.read(fpath)
            st_raw += temp_st
            loaded_files.append(fpath)
            print(f'  [成功讀取] {fpath} (包含 {len(temp_st)} 條波形記錄)')
        except Exception:
            # 不是有效 seismic 格式則略過
            continue

    if len(st_raw) == 0:
        raise RuntimeError('錯誤：未在目錄中找到任何有效的 MiniSEED 地震資料！')

    st_raw.merge(fill_value='interpolate')
    return st_raw, loaded_files


# ==========================================
# 3. 資料檢查與測站距離計算
# ==========================================
def analyze_stations(st):
    """
    分析 Stream 中的測站與分量，並對比簡報速查表檢查是否有缺失測站。
    """
    available_stations = sorted(list(set(tr.stats.station for tr in st)))
    station_channels = {}
    for tr in st:
        sta = tr.stats.station
        cha = tr.stats.channel
        station_channels.setdefault(sta, set()).add(cha)

    print('\n' + '=' * 65)
    print('資料庫包含測站與分量列表：')
    print('=' * 65)
    for sta in available_stations:
        lat, lon = STATION_COORDS.get(sta, (None, None))
        dist_str = '未知座標'
        if lat is not None:
            dist_m, _, _ = gps2dist_azimuth(EPICENTER[0], EPICENTER[1], lat, lon)
            dist_km = dist_m / 1000.0
            dist_str = f'{dist_km:6.2f} km'
        chs = ', '.join(sorted(list(station_channels[sta])))
        print(f'  測站 {sta:5s} | 震央距: {dist_str} | 分量: {chs}')

    # 檢查缺失測站
    missing_stations = [s for s in STATION_COORDS if s not in available_stations]
    print('-' * 65)
    if missing_stations:
        print(f'【注意：資料缺件回報】')
        for ms in missing_stations:
            lat, lon = STATION_COORDS[ms]
            d_m, _, _ = gps2dist_azimuth(EPICENTER[0], EPICENTER[1], lat, lon)
            print(f'  - 測站 {ms} (預估震央距 {d_m/1000.0:.2f} km)：在當前 MiniSEED 檔案中【未包含】此測站資料！')
    else:
        print('簡報中所有 10 個核心測站資料皆齊全！')
    print('=' * 65 + '\n')

    return available_stations, station_channels


# ==========================================
# 4. 繪製【圖一：震波距離剖面圖】
# ==========================================
def plot_figure_1_record_section(st_filt, output_dir='.'):
    """
    圖一：01_record_section_distance.png
    仿簡報第 4、6、8、10 頁風格。
    Y 軸為 Distance (km)，依震央距由近至遠排列；X 軸為相對時間 (10000 ~ 11200 秒)。
    標註 Bp 2-8Hz 與走時移動線 (波速參考線)。
    """
    t_start = T0 + 10000
    t_end = T0 + 11200
    st_crop = st_filt.slice(t_start, t_end)

    # 挑選垂直分量（優先 HLZ，次選 HHZ）
    vert_traces = {}
    for tr in st_crop:
        sta = tr.stats.station
        cha = tr.stats.channel
        if cha in ['HLZ', 'HHZ']:
            if sta not in vert_traces or (cha == 'HLZ' and vert_traces[sta].stats.channel != 'HLZ'):
                vert_traces[sta] = tr

    sorted_records = []
    for sta, tr in vert_traces.items():
        if sta in STATION_COORDS:
            lat, lon = STATION_COORDS[sta]
            d_m, _, _ = gps2dist_azimuth(EPICENTER[0], EPICENTER[1], lat, lon)
            sorted_records.append((d_m / 1000.0, sta, tr))

    sorted_records.sort(key=lambda x: x[0])

    colors = ['#ffcc00', '#00d2ff', '#00cc00', '#0000cc', '#e600e6', '#ff0000', '#000000', '#00b050', '#00c5cd']

    fig, ax = plt.subplots(figsize=(11, 7), dpi=300)

    for i, (d_km, sta, tr) in enumerate(sorted_records):
        t_rel = np.linspace(10000, 11200, len(tr.data))
        max_amp = np.max(np.abs(tr.data))
        norm_trace = (tr.data / max_amp) * 1.8 if max_amp > 0 else tr.data
        col = colors[i % len(colors)]

        # 水平基準線
        ax.axhline(d_km, color='gray', linestyle=':', lw=0.7, alpha=0.6)
        # 繪製波形
        ax.plot(t_rel, d_km - norm_trace, color=col, lw=0.65)

        # 右側測站標籤（仿簡報命名：強震儀標 ../acc/TW.STA，寬頻標 TW.STA.LOC.CHA）
        if tr.stats.channel.startswith('HL'):
            label = f'../acc/TW.{sta}'
        else:
            loc = tr.stats.location if tr.stats.location else '00'
            label = f'TW.{sta}.{loc}.{tr.stats.channel}'
        ax.text(11210, d_km, label, va='center', ha='left', fontsize=8.5, family='monospace')

    # 設定軸範圍與刻度（Y軸倒轉：0 在最上方）
    ax.set_ylim(70, 0)
    ax.set_xlim(10000, 11200)

    # 繪製走時參考線 (Moveout lines: 地震波與空氣衝擊波)
    t_blast = 10565.0
    d_eval = np.linspace(0, 65, 100)
    t_seismic = t_blast + d_eval / 3.5    # 地震波波速約 3.5 km/s
    t_acoustic = t_blast + d_eval / 0.34  # 空氣衝擊波音速約 0.34 km/s (340 m/s)

    ax.plot(t_seismic[t_seismic <= 11200], d_eval[t_seismic <= 11200], 'k-', lw=0.8, alpha=0.85)
    ax.plot(t_acoustic[t_acoustic <= 11200], d_eval[t_acoustic <= 11200], 'k-', lw=0.8, alpha=0.85)

    # 左上角粗體標註
    ax.text(0.04, 0.94, 'Bp 2-8Hz', transform=ax.transAxes, fontsize=15, fontweight='bold')

    ax.set_xlabel('Time (sec)', fontsize=11)
    ax.set_ylabel('Distance (km)', fontsize=11)
    ax.tick_params(direction='in', top=True, right=True, length=5)

    plt.subplots_adjust(left=0.08, right=0.84, top=0.96, bottom=0.09)
    out_path = os.path.join(output_dir, '01_record_section_distance.png')
    plt.savefig(out_path, dpi=300)
    plt.close(fig)
    print(f'[產出成功] 圖一：{os.path.abspath(out_path)}')
    return out_path


# ==========================================
# 5. 繪製【圖二：原始資料 vs 濾波資料對比圖】
# ==========================================
def plot_figure_2_original_vs_filtered(st_raw, st_filt, output_dir='.'):
    """
    圖二：02_original_vs_bp2-8Hz.png
    仿簡報第 8 vs 10 頁（以及第 4 vs 5 頁風格）。
    垂直雙子圖：上方為原始波形剖面（Original data），下方為 2-8 Hz 帶通濾波波形剖面（Bp 2-8Hz）。
    """
    t_start = T0 + 10000
    t_end = T0 + 11200
    st_raw_crop = st_raw.slice(t_start, t_end)
    st_filt_crop = st_filt.slice(t_start, t_end)

    vert_raw = {}
    vert_filt = {}
    for tr in st_raw_crop:
        sta, cha = tr.stats.station, tr.stats.channel
        if cha in ['HLZ', 'HHZ']:
            if sta not in vert_raw or (cha == 'HLZ' and vert_raw[sta].stats.channel != 'HLZ'):
                vert_raw[sta] = tr

    for tr in st_filt_crop:
        sta, cha = tr.stats.station, tr.stats.channel
        if cha in ['HLZ', 'HHZ']:
            if sta not in vert_filt or (cha == 'HLZ' and vert_filt[sta].stats.channel != 'HLZ'):
                vert_filt[sta] = tr

    sorted_records = []
    for sta in vert_raw:
        if sta in STATION_COORDS:
            lat, lon = STATION_COORDS[sta]
            d_m, _, _ = gps2dist_azimuth(EPICENTER[0], EPICENTER[1], lat, lon)
            sorted_records.append((d_m / 1000.0, sta))
    sorted_records.sort(key=lambda x: x[0])

    colors = ['#ffcc00', '#00d2ff', '#00cc00', '#0000cc', '#e600e6', '#ff0000', '#000000', '#00b050', '#00c5cd']

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9.5), sharex=True, sharey=True, dpi=300)

    for i, (d_km, sta) in enumerate(sorted_records):
        col = colors[i % len(colors)]
        tr_o = vert_raw[sta]
        tr_f = vert_filt[sta]

        t_rel = np.linspace(10000, 11200, len(tr_o.data))

        amp_o = np.max(np.abs(tr_o.data))
        norm_o = (tr_o.data / amp_o) * 1.8 if amp_o > 0 else tr_o.data

        amp_f = np.max(np.abs(tr_f.data))
        norm_f = (tr_f.data / amp_f) * 1.8 if amp_f > 0 else tr_f.data

        # 標籤
        if tr_o.stats.channel.startswith('HL'):
            label = f'../acc/TW.{sta}'
        else:
            loc = tr_o.stats.location if tr_o.stats.location else '00'
            label = f'TW.{sta}.{loc}.{tr_o.stats.channel}'

        # 上圖：Original data
        ax1.axhline(d_km, color='gray', linestyle=':', lw=0.6, alpha=0.6)
        ax1.plot(t_rel, d_km - norm_o, color=col, lw=0.6)
        ax1.text(11210, d_km, label, va='center', ha='left', fontsize=8, family='monospace')

        # 下圖：Bp 2-8Hz
        ax2.axhline(d_km, color='gray', linestyle=':', lw=0.6, alpha=0.6)
        ax2.plot(t_rel, d_km - norm_f, color=col, lw=0.6)
        ax2.text(11210, d_km, label, va='center', ha='left', fontsize=8, family='monospace')

    ax1.set_ylim(70, 0)
    ax1.set_xlim(10000, 11200)

    ax1.text(0.03, 0.93, 'Original data', transform=ax1.transAxes, fontsize=13, fontweight='bold')
    ax2.text(0.03, 0.93, 'Bp 2-8Hz', transform=ax2.transAxes, fontsize=13, fontweight='bold')

    for ax in (ax1, ax2):
        ax.set_ylabel('Distance (km)', fontsize=11)
        ax.tick_params(direction='in', top=True, right=True, length=5)

    ax2.set_xlabel('Time (sec)', fontsize=11)

    plt.subplots_adjust(left=0.08, right=0.84, top=0.96, bottom=0.06, hspace=0.10)
    out_path = os.path.join(output_dir, '02_original_vs_bp2-8Hz.png')
    plt.savefig(out_path, dpi=300)
    plt.close(fig)
    print(f'[產出成功] 圖二：{os.path.abspath(out_path)}')
    return out_path


# ==========================================
# 6. 繪製【圖三：近場三分量波形時序圖】
# ==========================================
def plot_figure_3_near_field(st_filt, output_dir='.'):
    """
    圖三：03_near_field_3components.png
    仿簡報第 13 頁與第 17 頁（Page 9 六分量）。
    針對近場測站 KAU (HLE, HLN, HLZ) 與 SGL (HLE, HLN, HLZ) 上下垂直分割 6 子圖。
    時間鎖定在 10500 ~ 10800 秒，右上角附帶 SAC 標籤。
    """
    t_start = T0 + 10500
    t_end = T0 + 10800
    st_crop = st_filt.slice(t_start, t_end)

    target_channels = [
        ('KAU', 'HLE', '#000000'),
        ('KAU', 'HLN', '#cc0000'),
        ('KAU', 'HLZ', '#00aa00'),
        ('SGL', 'HLE', '#0000cc'),
        ('SGL', 'HLN', '#d4a000'),
        ('SGL', 'HLZ', '#00c5cd')
    ]

    fig, axes = plt.subplots(len(target_channels), 1, figsize=(10, 8.5), sharex=True,
                             gridspec_kw={'hspace': 0.0}, dpi=300)

    for i, (sta, cha, col) in enumerate(target_channels):
        ax = axes[i]
        matched = st_crop.select(station=sta, channel=cha)
        if len(matched) == 0:
            continue
        tr = matched[0]
        time_vec = np.linspace(10500, 10800, len(tr.data))

        # 自動量程判斷與 y 軸標籤（X 10+3 或 X 10+2）
        max_val = np.max(np.abs(tr.data))
        if max_val > 500:
            scale = 1000.0
            scale_str = 'X 10+3'
        elif max_val > 50:
            scale = 100.0
            scale_str = 'X 10+2'
        else:
            scale = 1.0
            scale_str = ''

        scaled_data = tr.data / scale
        ax.plot(time_vec, scaled_data, color=col, lw=0.65)
        ax.set_xlim(10500, 10800)

        # 動態設定對稱 Y 軸刻度範圍
        y_lim = np.ceil(np.max(np.abs(scaled_data)) * 1.3)
        if y_lim == 0:
            y_lim = 1.0
        ax.set_ylim(-y_lim, y_lim)
        ax.set_ylabel(scale_str, fontsize=8.5)

        ax.tick_params(direction='in', top=True, right=True, length=4.5)

        # 右側 SAC 樣式文字註解
        sac_text = f"EVENTID\n{sta}  {cha}\nJUL 31 (212), 2014\n13:00:00.000"
        ax.text(0.985, 0.90, sac_text, transform=ax.transAxes, ha='right', va='top',
                fontsize=7.5, family='monospace', linespacing=1.1,
                bbox=dict(boxstyle='square,pad=0.15', facecolor='white', alpha=0.8, edgecolor='none'))

    axes[-1].set_xlabel('Time (sec)', fontsize=11)
    axes[-1].set_xticks(range(10500, 10801, 50))

    plt.subplots_adjust(left=0.11, right=0.96, top=0.96, bottom=0.07)
    out_path = os.path.join(output_dir, '03_near_field_3components.png')
    plt.savefig(out_path, dpi=300)
    plt.close(fig)
    print(f'[產出成功] 圖三：{os.path.abspath(out_path)}')
    return out_path


# ==========================================
# 7. 繪製【圖四：核心站時頻譜圖 (Spectrogram)】
# ==========================================
def plot_figure_4_spectrogram(st_raw, st_filt, output_dir='.'):
    """
    圖四：04_spectrogram_kau.png
    仿簡報第 15 頁與第 16 頁（Page 11 KAU HLZ）。
    上半部為 2-8 Hz 濾波時序波形（X 軸 10500 ~ 10800 秒）。
    下半部為 Spectrogram（0 ~ 20 Hz），彩虹色階突顯爆炸高頻能量脈衝。
    """
    t_start = T0 + 10500
    t_end = T0 + 10800

    # 優先挑選 KAU HLZ，若無則挑選 SNJ HHZ
    sta_choice, cha_choice = 'KAU', 'HLZ'
    matched_raw = st_raw.select(station=sta_choice, channel=cha_choice)
    matched_filt = st_filt.select(station=sta_choice, channel=cha_choice)
    if len(matched_raw) == 0:
        sta_choice, cha_choice = 'SNJ', 'HHZ'
        matched_raw = st_raw.select(station=sta_choice, channel=cha_choice)
        matched_filt = st_filt.select(station=sta_choice, channel=cha_choice)

    tr_raw = matched_raw[0].slice(t_start, t_end)
    tr_filt = matched_filt[0].slice(t_start, t_end)

    # 計算 Spectrogram (STFT)
    fs = tr_raw.stats.sampling_rate
    nperseg = 256
    noverlap = 240
    f, t_spec, Sxx = signal.spectrogram(tr_raw.data, fs=fs, nperseg=nperseg, noverlap=noverlap)
    t_spec_rel = t_spec + 10500

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.5),
                                   gridspec_kw={'height_ratios': [1, 2.4], 'hspace': 0.08},
                                   sharex=True, dpi=300)

    # 上半部：濾波波形
    time_vec = np.linspace(10500, 10800, len(tr_filt.data))
    ax1.plot(time_vec, tr_filt.data / 1000.0, 'k-', lw=0.75)
    ax1.set_xlim(10500, 10800)
    ax1.set_ylim(-2.0, 2.0)
    ax1.set_ylabel('X 10+3', fontsize=9)
    ax1.tick_params(direction='in', top=True, right=True, length=5)

    # SAC 標籤
    sac_text = f"EVENTID\n{sta_choice}  {cha_choice}\nJUL 31 (212), 2014\n13:00:00.000"
    ax1.text(0.985, 0.88, sac_text, transform=ax1.transAxes, ha='right', va='top',
            fontsize=8, family='monospace', linespacing=1.1,
            bbox=dict(boxstyle='square,pad=0.15', facecolor='white', alpha=0.8, edgecolor='none'))

    # 下半部：時頻譜 (Spectrogram 0 - 20 Hz)
    mask_f = f <= 20.0

    # 建立 Yamada 簡報風格彩虹色彩映射 (淡藍底 -> 綠 -> 黃 -> 紅 -> 洋紅 -> 白)
    colors = [
        (0.0, '#00d2ff'),
        (0.05, '#00f0ff'),
        (0.18, '#00ff00'),
        (0.38, '#ffff00'),
        (0.62, '#ff0000'),
        (0.85, '#ff00ff'),
        (1.0, '#ffffff')
    ]
    yamada_rainbow = mcolors.LinearSegmentedColormap.from_list('yamada_rainbow', colors)

    im = ax2.pcolormesh(t_spec_rel, f[mask_f], Sxx[mask_f, :], cmap=yamada_rainbow,
                        shading='gouraud', vmin=0, vmax=2e5)
    ax2.set_ylim(0, 20)
    ax2.set_yticks([0, 5, 10, 15, 20])
    ax2.set_xlabel('Time (sec)', fontsize=11)
    ax2.set_ylabel('Frequency (Hz)', fontsize=11)
    ax2.tick_params(direction='in', top=True, right=True, length=5)

    # 色階條（對齊簡報左側標示 X 10+5）
    cbar_ax = fig.add_axes([0.045, 0.15, 0.02, 0.45])
    cbar = fig.colorbar(im, cax=cbar_ax)
    cbar.set_ticks([0, 5e4, 1e5, 1.5e5, 2e5])
    cbar.set_ticklabels(['0', '', '1', '', '2'])
    cbar_ax.set_ylabel('X 10+5', fontsize=8.5)
    cbar_ax.yaxis.set_label_position('left')
    cbar_ax.yaxis.tick_left()

    plt.subplots_adjust(left=0.14, right=0.96, top=0.95, bottom=0.09)
    out_path = os.path.join(output_dir, '04_spectrogram_kau.png')
    plt.savefig(out_path, dpi=300)
    plt.close(fig)
    print(f'[產出成功] 圖四：{os.path.abspath(out_path)}')
    return out_path


# ==========================================
# 主程式執行流程
# ==========================================
def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = script_dir

    print('\n' + '#' * 65)
    print('【2014 高雄氣爆地震資料分析 - Masumi Yamada 簡報復刻腳本】')
    print('#' * 65)

    # 1. 搜尋並載入檔案
    st_raw, loaded_files = find_and_load_mseed_files(script_dir)

    # 2. 去平均與去線性 (Demean & Linear Detrend)
    print('\n[資料前處理] 執行去均值 (demean) 與去線性漂移 (linear)...')
    st_raw.detrend('demean')
    st_raw.detrend('linear')

    # 3. 帶通濾波 (Bandpass 2.0 - 8.0 Hz)
    print('[資料前處理] 執行帶通濾波 (bandpass 2-8 Hz, corners=4, zerophase=True)...')
    st_filt = st_raw.copy()
    st_filt.filter('bandpass', freqmin=2.0, freqmax=8.0, corners=4, zerophase=True)

    # 4. 分析測站分量與報告缺件
    analyze_stations(st_raw)

    # 5. 依序產生四大圖表
    print('=' * 65)
    print('開始繪製高品質 300 DPI 圖表：')
    print('=' * 65)
    f1 = plot_figure_1_record_section(st_filt, output_dir)
    f2 = plot_figure_2_original_vs_filtered(st_raw, st_filt, output_dir)
    f3 = plot_figure_3_near_field(st_filt, output_dir)
    f4 = plot_figure_4_spectrogram(st_raw, st_filt, output_dir)

    print('\n' + '=' * 65)
    print('【全部圖表生成完畢！】')
    print(f'1. 震波距離剖面圖: {f1}')
    print(f'2. 原始 vs 濾波對比: {f2}')
    print(f'3. 近場三分量波形: {f3}')
    print(f'4. 核心站時頻譜圖: {f4}')
    print('=' * 65 + '\n')


if __name__ == '__main__':
    main()
