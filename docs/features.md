Contents

[1 Ngữ cảnh thiết kế 2](#_Toc226579428)

[2 Layer 1: Hard Filter 3](#_Toc226579429)

[3 Layer 2: BUY Scoring 5](#_Toc226579430)

[3.1 Điểm Thanh khoản (0-100) 5](#_Toc226579431)

[3.1.1 Điểm GTGD20 5](#_Toc226579432)

[3.1.2 Điểm hoạt động intraday 6](#_Toc226579433)

[3.1.3 Điểm ổn định thanh khoản - CV 6](#_Toc226579434)

[3.2 Điểm Động lượng (0-100) 7](#_Toc226579435)

[3.2.1 Điểm biến động giá đa khung (trọng số 0.3) 7](#_Toc226579436)

[3.2.2 Điểm phân tích MA 8](#_Toc226579437)

[3.2.3 Điểm sức mạnh tương đối vs VN-Index 9](#_Toc226579438)

[3.2.4 Điểm tích lũy/phân phối (A/D Ratio) 10](#_Toc226579439)

[3.2.5 Điểm xác nhận kỹ thuật (RSI + MACD) 11](#_Toc226579440)

[3.3 Điểm Breakout (0.35) 12](#_Toc226579441)

[3.3.1 Điểm vượt cản giá 12](#_Toc226579442)

[3.3.2 Điểm xác nhận volume breakout 12](#_Toc226579443)

[3.3.3 Điểm volume dry-up trước breakout 13](#_Toc226579444)

[3.3.4 Điểm chất lượng nền giá (Base Quality) 13](#_Toc226579445)

[3.3.5 Điểm giữ giá sau breakout 14](#_Toc226579446)

# Ngữ cảnh thiết kế

**Mục đích:** Tìm cổ phiếu đang breakout với thanh khoản đủ để vào/ra nhanh, phục vụ lướt sóng.
**Không phải:** Đầu tư cơ bản, cổ tức, tăng trưởng dài hạn.

Điều này ảnh hưởng trực tiếp đến thiết kế:

- Thanh khoản weighted cao - vào/ra phải trơn tru, không bị trượt giá
- Breakout là thời điểm vào lệnh - cần chất lượng cao, không mua sớm
- Technical signals là tất cả - fundamental không liên quan với timeframe vài ngày
- Market regime là gate - không mua khi thị trường downtrend dù mã tốt đến đâu

# Layer 1: Hard Filter

Mục tiêu: Loại nhanh các mã không đủ điều kiện tối thiểu **trước khi** tốn thời gian tính điểm.

| **#** | **Filter**               | **Điều kiện**                                                   | **Lý do**                                                                                                                                                                                                                                                                                                                                                                                                                          | **Nguồn**                        |
| ----- | ------------------------ | --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| 1     | **Sàn**                  | HOSE + HNX                                                      | UPCOM tiêu chuẩn niêm yết thấp, thanh khoản mỏng, rủi ro thao túng cao - không phù hợp lướt sóng                                                                                                                                                                                                                                                                                                                                   | Thiết kế gốc                     |
| 2     | **Trạng thái giao dịch** | Không cảnh báo / kiểm soát / tạm ngừng                          | Cổ phiếu ST, HL, tạm ngừng không thể giao dịch bình thường - mọi tín hiệu đều giả                                                                                                                                                                                                                                                                                                                                                  | Thiết kế gốc                     |
| 3     | **Lịch sử dữ liệu**      | ≥ 60 phiên giao dịch                                            | Cần đủ data cho MA20 (20 phiên), slope (thêm 5), CV (20 phiên), RS 1 tháng (21 phiên), volume dry-up (5 phiên) - 60 phiên là buffer an toàn                                                                                                                                                                                                                                                                                        | Thiết kế gốc                     |
| 4     | **Giá tối thiểu**        | ≥ 5,000 VND                                                     | Lọc penny stock - giá quá thấp dễ bị làm giá, spread rộng, không phản ánh cung cầu thật                                                                                                                                                                                                                                                                                                                                            | Thiết kế gốc                     |
| 5     | **GTGD20**               | ≥ 20 tỷ VND                                                     | Ngưỡng tối thiểu để lướt sóng khả thi - vào/ra không bị trượt giá lớn. 20 tỷ tương ứng điểm 60 trong scoring, nhất quán với hệ thống                                                                                                                                                                                                                                                                                               | Thiết kế gốc                     |
| 6     | **Intraday active**      | GTGD hôm nay ≥ 30% GTGD kỳ vọng (time-adjusted)                 | Mã có thanh khoản nền tốt nhưng hôm nay không ai giao dịch → không có setup thật. Loại trước khi tốn API call                                                                                                                                                                                                                                                                                                                      | Thiết kế gốc                     |
| 7     | **Giá trần / sàn**       | Không đang ở giá trần hoặc sàn                                  | Mã ở trần: không thể mua (full bid), breakout signal là nhiễu. Mã ở sàn: không thể thoát - không phù hợp lướt sóng                                                                                                                                                                                                                                                                                                                 | Bổ sung mới                      |
| 8     | **CV cap**               | CV < 200%                                                       | CV = std(GTGD_20_sessions) / mean(GTGD_20_sessions) × 100<br><br>Đo mức độ thất thường của thanh khoản trong 20 phiên - CV càng cao = thanh khoản càng không đều.<br><br>Lọc mã có 1-2 phiên volume đột biến rồi chết - GTGD20 bị kéo cao giả. Bẫy thanh khoản phổ biến ở VN <br>VN market: pump-and-dump thường tạo 1-2 phiên volume cực lớn để kéo GTGD20 lên, sau đó quay về mỏng. CV cap là lớp bảo vệ chống lại kiểu bẫy này. | Bổ sung mới                      |
| 9     | **Data sạch**            | OHLCV đủ                                                        | Thiếu data sẽ làm sai MA20, High20, CV - cho điểm không tin cậy                                                                                                                                                                                                                                                                                                                                                                    | Thiết kế gốc                     |
| 10    | **Market Regime Gate**   | VN-Index không trong downtrend rõ ràng (xem công thức bên dưới) | "3 trong 4 cổ phiếu đi theo xu hướng thị trường" - O'Neil. Lướt sóng trong bear market xác suất thắng giảm mạnh dù mã có BUY score cao                                                                                                                                                                                                                                                                                             | **Học từ CANSLIM (M component)** |

**Cách tính Marget Regime Gate (Item 10)**

vnindex_ma20 = mean(vnindex_close, 20)

vnindex_ma5 = mean(vnindex_close, 5)

_\# Downtrend rõ ràng: VN-Index dưới MA20 > 3% VÀ MA5 đang dốc xuống_

if (vnindex_close / vnindex_ma20 < 0.97) and (vnindex_ma5 < vnindex_ma20):

→ SKIP toàn bộ universe, không chạy screener

→ Ghi log: "Market in downtrend - screener suspended"

_\# Thị trường choppy (0.97-1.00): chạy screener nhưng cảnh báo_

elif vnindex_close / vnindex_ma20 < 1.00:

→ Chạy bình thường nhưng thêm cảnh báo "MARKET CAUTION" vào output

_\# Thị trường uptrend (> 1.00): chạy bình thường_

# Layer 2: BUY Scoring

BUY Score = 0.35 × Điểm Thanh khoản

\+ 0.30 × Điểm Động lượng

\+ 0.35 × Điểm Breakout

| **BUY Score** | **Ý nghĩa** | **Hành động gợi ý** |
| ------------- | ----------- | ------------------- |
| 85-100        | Rất mạnh    | Ưu tiên cao nhất    |
| 75-84         | Mạnh        | Theo dõi sát        |
| 65-74         | Khá         | Watchlist           |
| 50-64         | Trung bình  | Không ưu tiên       |
| < 50          | Yếu         | Bỏ qua              |

## Điểm Thanh khoản (0-100)

_Ý nghĩa: Cổ phiếu này có đủ dòng tiền thật, đủ ổn định, và hôm nay đang hoạt động để lướt sóng không?_

Điểm thanh khoản = 0.55 × Điểm GTGD20

\+ 0.30 × Điểm hoạt động intraday

\+ 0.15 × Điểm ổn định thanh khoản (CV)

### Điểm GTGD20

_Quy mô tiền giao dịch nền - mã này bình thường có đủ tiền quay vòng không?_

GTGD_ngay = close × volume

GTGD20 = mean(GTGD_ngay, 20_phiên)

| **GTGD20** | **Điểm** | **Phân loại**                       |
| ---------- | -------- | ----------------------------------- |
| ≥ 100 tỷ   | 100      | Thanh khoản cực cao (VCB, HPG, VHM) |
| 50-100 tỷ  | 80       | Thanh khoản cao                     |
| 20-50 tỷ   | 60       | Thanh khoản khá                     |
| 5-20 tỷ    | 40       | Trung bình                          |
| 1-5 tỷ     | 20       | Thấp                                |
| < 1 tỷ     | 0        | Rất thấp                            |

### Điểm hoạt động intraday

_Hôm nay có dòng tiền vào không - không chỉ thanh khoản nền mà còn hôm nay cụ thể?_

GTGD_intraday = price_hiện_tại × volume_intraday

time_ratio = minutes_elapsed / 225 # 225 phút thực giao dịch (loại ATO 15ph + ATC 15ph)

GTGD_kỳ_vọng = GTGD20 × time_ratio

intraday_ratio = GTGD_intraday / GTGD_kỳ_vọng

_225 phút = Sáng (9:15-11:30 = 135ph) + Chiều (13:00-14:45 = 105ph) - loại ATO và ATC_

| **Intraday ratio** | **Điểm** | **Ý nghĩa**             |
| ------------------ | -------- | ----------------------- |
| ≥ 200%             | 100      | Cực kỳ sôi động         |
| 150-200%           | 80       | Rất tích cực            |
| 100-150%           | 60       | Tốt                     |
| 60-100%            | 40       | Bình thường             |
| 30-60%             | 20       | Yếu                     |
| < 30%              | 0        | Gần như không giao dịch |

### Điểm ổn định thanh khoản - CV

_Thanh khoản đều đặn hay chỉ bùng lên vài phiên - phân biệt thanh khoản thật vs bẫy volume?_

CV = std(GTGD_20_phiên) / mean(GTGD_20_phiên) × 100

| **CV**   | **Điểm** |
| -------- | -------- |
| < 30%    | 100      |
| 30-50%   | 80       |
| 50-75%   | 60       |
| 75-100%  | 40       |
| 100-150% | 20       |
| ≥ 150%   | 0        |

## Điểm Động lượng (0-100)

_Ý nghĩa: Phân biệt mã thanh khoản tốt nhưng đi ngang với mã đang tăng thật. Với lướt sóng, chỉ cần bắt được đà đang mạnh - không cần dự báo dài hạn._

Điểm động lượng = 0.30 × Điểm biến động giá composite

\+ 0.20 × Điểm phân tích MA

\+ 0.20 × Điểm sức mạnh tương đối (RS) ← học từ VCP

\+ 0.15 × Điểm tích lũy/phân phối (A/D) ← học từ CANSLIM

\+ 0.15 × Điểm xác nhận kỹ thuật (RSI+MACD)

### Điểm biến động giá đa khung (trọng số 0.3)

_Mã có đang chạy mạnh hơn bình thường không - xét đa khung thời gian để lọc noise?_

return_1d = (close_hôm_nay - close_1d_trước) / close_1d_trước × 100

return_5d = (close_hôm_nay - close_5d_trước) / close_5d_trước × 100

return_20d = (close_hôm_nay - close_20d_trước) / close_20d_trước × 100

composite = 0.50 × return_1d + 0.30 × return_5d + 0.20 × return_20d

_(Trọng số 50/30/20: Lướt sóng ưu tiên tín hiệu ngắn nhất, nhưng 5D và 20D xác nhận momentum có nền.)_

| **Composite return** | **Điểm** |
| -------------------- | -------- |
| < 0%                 | 0        |
| 0-1%                 | 20       |
| 1-2%                 | 40       |
| 2-4%                 | 60       |
| 4-7%                 | 80       |
| \> 7%                | 100      |

### Điểm phân tích MA

Điểm này đo 2 thứ

**1\. Vị trí giá so với MA - "Giá đang ở đâu?"**

Giá > MA50 > MA20 → Bullish alignment → điểm cao

Giá < MA20 → Yếu → điểm thấp/0

Ý nghĩa thực tế:

- **Giá trên MA20:** Xu hướng ngắn hạn đang lên
- **Giá trên MA50:** Xu hướng trung hạn đang lên
- Mã breakout nhưng giá vẫn dưới MA50 → breakout yếu, chưa đủ momentum

**2\. Độ dốc MA20 - "Momentum có đang tăng tốc không?"**

slope_pct = (MA20_hôm_nay - MA20_cách_5_phiên) / MA20_cách_5_phiên × 100

Ý nghĩa thực tế:

- **Slope dương mạnh:** MA20 đang dốc lên → xu hướng tăng có gia tốc
- **Slope gần 0:** MA20 đi ngang → mã thanh khoản tốt nhưng momentum thật sự chưa có
- **Slope âm:** MA20 đang dốc xuống → tránh, dù giá hôm nay tăng

_cả hai cùng trả lời một câu hỏi:_ **_"Xu hướng của mã này có thật và đang tăng tốc không?"_**

**Ví dụ:**

Mã A: Giá +3% hôm nay, nhưng giá < MA20, MA20 đang dốc xuống

→ Tăng 1 phiên, không có momentum thật → điểm MA thấp

Mã B: Giá +2% hôm nay, giá > MA20 > MA50, MA20 slope +0.6%

→ Tăng có nền tảng, momentum đang xây dựng → điểm MA cao

ma20 = mean(close, 20)

ma50 = mean(close, 50)

slope_pct = (ma20_today - ma20_5d_ago) / ma20_5d_ago × 100 # chuẩn hóa %

price_vs_ma20 = (close_today - ma20) / ma20 × 100

price_vs_ma50 = (close_today - ma50) / ma50 × 100

_Bảng điểm áp dụng chung cho cả MA20 và MA50:_

| **% so với MA** | **Điểm** |
| --------------- | -------- |
| Dưới MA (< 0%)  | 0        |
| 0-2% trên       | 40       |
| 2-5% trên       | 70       |
| \> 5% trên      | 100      |

_Slope MA20:_

| **Slope%** | **Điểm** |
| ---------- | -------- |
| < 0%       | 0        |
| 0-0.2%     | 30       |
| 0.2-0.5%   | 60       |
| \> 0.5%    | 100      |

score_ma = 0.35 × score(price_vs_ma20) + 0.30 × score(price_vs_ma50) + 0.35 × score(slope_pct)

### Điểm sức mạnh tương đối vs VN-Index

_Tham khảo từ: VCP - Relative Strength component (15% weight trong VCP)_

_Phương pháp VCP phát hiện rằng các "leading stock" luôn outperform index trước khi breakout. Mã breakout nhưng tăng ít hơn VN-Index trong 3 tháng = không phải leader, xác suất thành công thấp hơn. Với lướt sóng, chỉ chơi mã đang dẫn dắt thị trường._

_\# Ưu tiên 3 tháng gần nhất cho lướt sóng (VCP dùng 12 tháng cho swing dài hơn)_

rs_3m = stock_return_3M - vnindex_return_3M

rs_1m = stock_return_1M - vnindex_return_1M

rs_weighted = 0.60 × rs_3m + 0.40 × rs_1m

trong đó

stock_return_3M = % thay đổi giá của cổ phiếu trong 3 tháng gần nhất.

stock_return_3M = (close_today - close_63d_ago) / close_63d_ago × 100

_(63 phiên giao dịch ≈ 3 tháng (21 phiên/tháng × 3)_

\`\`\`

vnindex_return_3M = (vnindex_close_today - vnindex_close_63d_ago) / vnindex_close_63d_ago × 100

| **RS weighted** | **Điểm** | **Ý nghĩa**          |
| --------------- | -------- | -------------------- |
| \> +10%         | 100      | Leader rõ ràng       |
| +5 đến +10%     | 80       | Outperform tốt       |
| 0 đến +5%       | 60       | Nhỉnh hơn index      |
| \-5 đến 0%      | 40       | Underperform nhẹ     |
| < -5%           | 20       | Yếu hơn index rõ rệt |

### Điểm tích lũy/phân phối (A/D Ratio)

_Tham khảo từ: CANSLIM - S component (Supply & Demand, 15% weight). CANSLIM S component phát hiện smart money đang mua hay bán. Nếu volume ngày tăng giá > volume ngày giảm giá → tổ chức đang tích lũy → momentum có nền tảng. Đây là tín hiệu SỚM hơn breakout, giúp phân biệt breakout có dòng tiền thật hay không._

_20 phiên gần nhất (điều chỉnh từ 60 phiên của CANSLIM - phù hợp lướt sóng ngắn hạn hơn)_

up_days_vol = \[volume\[i\] for i in range(20) if close\[i\] > close\[i-1\]\]

down_days_vol = \[volume\[i\] for i in range(20) if close\[i\] < close\[i-1\]\]

ad_ratio = mean(up_days_vol) / mean(down_days_vol)

| **A/D ratio** | **Điểm** | **Ý nghĩa**                     |
| ------------- | -------- | ------------------------------- |
| ≥ 2.0         | 100      | Tích lũy mạnh (smart money vào) |
| 1.5-2.0       | 80       | Tích lũy rõ ràng                |
| 1.0-1.5       | 60       | Trung tính / tích lũy nhẹ       |
| 0.7-1.0       | 40       | Phân phối nhẹ                   |
| < 0.7         | 20       | Phân phối rõ (smart money ra)   |

### Điểm xác nhận kỹ thuật (RSI + MACD)

RSI 14 phiên

| **RSI (14 phiên)** | **Điểm** | **Ghi chú**                                                                         |
| ------------------ | -------- | ----------------------------------------------------------------------------------- |
| < 50               | 20       | Lực yếu                                                                             |
| 50-60              | 50       | Trung tính                                                                          |
| 60-70              | 80       | Momentum tốt                                                                        |
| \> 70              | 100      | Momentum mạnh - _với lướt sóng, RSI > 70 là dấu hiệu tốt chứ không phải overbought_ |

MACD - chuẩn hóa theo giá:

histogram = macd_line - signal_line

histogram_pct = histogram / close_today × 100

| **Histogram%** | **Điểm** |
| -------------- | -------- |
| < 0%           | 20       |
| 0-0.05%        | 50       |
| \> 0.05%       | 100      |

## Điểm Breakout (0.35)

**_Mục tiêu:_** _Xác định giá đang vượt vùng kháng cự với xác nhận đủ mạnh. Với lướt sóng, đây là trigger để vào lệnh - phải chính xác và đủ tin cậy._

**Gate condition (quan trọng):**

if breakout_ratio < 1.0:

return breakout_score = 0 # Chưa breakout → toàn bộ Breakout score = 0

_Lý do: Các sub-component còn lại (volume dry-up, base quality, holding) đều vô nghĩa khi chưa có breakout._

Điểm breakout = 0.30 × Điểm vượt cản giá

\+ 0.25 × Điểm xác nhận volume breakout

\+ 0.20 × Điểm volume dry-up trước breakout ← học từ VCP

\+ 0.15 × Điểm chất lượng nền giá ← học từ VCP

\+ 0.10 × Điểm giữ giá sau breakout

### Điểm vượt cản giá

High20 = max(high, 20_sessions) # không tính hôm nay

breakout_ratio = close_today / High20

| **Breakout ratio** | **Điểm**          |
| ------------------ | ----------------- |
| < 1.00             | Gate: toàn bộ = 0 |
| 1.00-1.01          | 40                |
| 1.01-1.02          | 70                |
| \> 1.02            | 100               |

### Điểm xác nhận volume breakout

\# Điều chỉnh thời gian để so sánh công bằng

volume_expected = avg_volume_20d × (minutes_elapsed / 225)

volume_ratio = volume_intraday / volume_expected

| **Volume ratio** | **Điểm** |
| ---------------- | -------- |
| < 1.0            | 20       |
| 1.0-1.3          | 50       |
| 1.3-1.8          | 80       |
| \> 1.8           | 100      |

### Điểm volume dry-up trước breakout

_Học từ: VCP - Volume Pattern component (20% weight trong VCP)_

_Lý do bổ sung: VCP phát hiện điều ngược lại với intuition: volume phải GIẢM trước breakout. Volume giảm = sellers đang cạn kiệt = supply đang cạn = khi buyers vào thì không có áp lực bán chặn lại → breakout bền vững hơn. Breakout với volume trước đó luôn cao = sellers vẫn còn nhiều = dễ bị chặn lại_.

\# Volume trung bình 4 phiên trước hôm nay (loại hôm nay vì đang breakout)

pre_vol_avg = mean(volume\[-5:-1\]) # 4 phiên gần nhất trước T0

dry_up_ratio = pre_vol_avg / avg_volume_20d

\# Thấp hơn = dry-up tốt hơn → sellers đang rút lui

| **Dry-up ratio** | **Điểm** | **Ý nghĩa**                                |
| ---------------- | -------- | ------------------------------------------ |
| < 0.5            | 100      | Sellers gần hết - breakout rất tin cậy     |
| 0.5-0.7          | 80       | Dry-up tốt                                 |
| 0.7-0.9          | 60       | Dry-up vừa                                 |
| 0.9-1.1          | 40       | Volume bình thường - bình thường           |
| \> 1.1           | 20       | Sellers vẫn đang bán - breakout rủi ro cao |

### Điểm chất lượng nền giá (Base Quality)

_Học từ: VCP - Contraction Quality component (25% weight trong VCP)_

_Lý do bổ sung: VCP yêu cầu nền giá phải ngày càng thu hẹp (volatility contraction) trước breakout. Breakout từ nền loạn (biên độ cao, không ổn định) dễ là fake breakout hơn nhiều. Với lướt sóng, nền giá chặt = điểm vào rõ ràng, stop-loss gần = risk/reward tốt hơn._

\# ATR (Average True Range) đơn giản = High - Low

atr_5d = mean(high\[-5:\] - low\[-5:\]) # biên độ trung bình 5 phiên gần nhất

atr_20d = mean(high\[-20:\] - low\[-20:\]) # biên độ trung bình 20 phiên

narrowing_ratio = atr_5d / atr_20d

\# < 1.0 = biên độ đang thu hẹp = nền đang chặt lại → breakout tin cậy hơn

| **Narrowing ratio** | **Điểm** | **Ý nghĩa**                                 |
| ------------------- | -------- | ------------------------------------------- |
| < 0.5               | 100      | Nền cực chặt - VCP textbook                 |
| 0.5-0.7             | 80       | Nền tốt                                     |
| 0.7-0.9             | 60       | Nền vừa phải                                |
| 0.9-1.1             | 40       | Biên độ ổn định, không co lại               |
| \> 1.1              | 20       | Biên độ mở rộng - nền loạn, breakout rủi ro |

### Điểm giữ giá sau breakout

&nbsp;_Nhiều mã vượt cản đầu phiên nhưng cuối phiên tụt lại - đặc biệt phổ biến trên sàn VN nơi lực xả kỹ thuật mạnh. Holding ratio phân biệt được breakout thật/giả trong cùng phiên._

\# t_breakout = thời điểm đầu tiên giá > High20

minutes_above_high20 = đếm số phút close > High20 từ t_breakout đến hiện tại

minutes_since_breakout = phút từ t_breakout đến hiện tại

holding_ratio = minutes_above_high20 / minutes_since_breakout

| **Holding ratio** | **Điểm** |
| ----------------- | -------- |
| \> 90%            | 100      |
| 70-90%            | 80       |
| 50-70%            | 60       |
| 30-50%            | 40       |
| < 30%             | 20       |
