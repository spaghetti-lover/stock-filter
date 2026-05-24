Contents

[1 Ngữ cảnh thiết kế 3](#_Toc230101552)

[2 Layer 1: Hard Filter 4](#_Toc230101553)

[3 Layer 2: BUY Scoring 6](#_Toc230101554)

[3.1 Điểm Thanh khoản (0-100) 6](#_Toc230101555)

[3.1.1 Điểm GTGD20 6](#_Toc230101556)

[3.1.2 Điểm hoạt động intraday 7](#_Toc230101557)

[3.1.3 Điểm ổn định thanh khoản - CV 8](#_Toc230101558)

[3.2 Điểm Động lượng (0-100) 8](#_Toc230101559)

[3.2.1 Điểm biến động giá đa khung (trọng số 0.3) 9](#_Toc230101560)

[3.2.2 Điểm phân tích MA 9](#_Toc230101561)

[3.2.3 Điểm sức mạnh tương đối vs VN-Index 11](#_Toc230101562)

[3.2.4 Điểm tích lũy/phân phối (A/D Ratio) 12](#_Toc230101563)

[3.2.5 Điểm Smart Money Flow 13](#_Toc230101564)

[3.2.6 Điểm xác nhận kỹ thuật score_technical (RSI + MACD) 14](#_Toc230101565)

[3.3 Điểm Breakout (0.35) 15](#_Toc230101566)

[3.3.1 Điểm vượt cản giá 15](#_Toc230101567)

[3.3.2 Điểm xác nhận volume breakout 15](#_Toc230101568)

[3.3.3 Điểm volume dry-up trước breakout 16](#_Toc230101569)

[3.3.4 Điểm chất lượng nền giá (Base Quality) 16](#_Toc230101570)

[3.3.5 Điểm sức mạnh đóng cửa (closing_strength) 17](#_Toc230101571)

[3.3.6 Hệ số đánh giá rủi ro bị khóa T+2.5 (risk_ratio) 18](#_Toc230101572)

[3.4 Tần suất chạy các tham số 19](#_Toc230101573)

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

\_Trả lời câu hỏi: Với quy mô lệnh của tôi, mã này có đủ thanh khoản để vào/ra mà không bị trượt giá không?\_GTGD_ngay = close × volume

GTGD20 = mean(GTGD_ngay, 20_phiên)

GTGD20 dùng 20 phiên trước đó (T-1 đến T-20), không bao gồm hôm nay → giá trị cố định trong ngày. Chỉ chạy 1 lần khi mở phiên

**safety_ratio = GTGD20 / position_size**

Tham số đầu vào:

- position_size: Số tiền tối đa bạn vào 1 mã (VND). Mặc định: 50,000,000 VND. (đưa tham số này vào phần setting)

| **Safety ratio** | **Điểm** | **Ý nghĩa**                                         |
| ---------------- | -------- | --------------------------------------------------- |
| ≥ 200×           | 100      | Lệnh chìm trong dòng tiền thị trường - vào/ra tự do |
| 100-200×         | 80       | Rất thoải mái, không lo trượt giá                   |
| 50-100×          | 60       | Tốt, trượt giá không đáng kể                        |
| 20-50×           | 40       | Chấp nhận được, có thể cần chia lệnh                |
| 10-20×           | 20       | Rủi ro trượt giá rõ rệt, cẩn thận khi thoát         |
| < 10×            | 0        | Không nên vào - lệnh quá lớn so với thị trường      |

### Điểm hoạt động intraday

_Hôm nay có dòng tiền vào không - không chỉ thanh khoản nền mà còn hôm nay cụ thể?_

GTGD_intraday = price_hiện_tại × volume_intraday

Volume_intraday: tổng số cổ phiếu được khớp từ đầu phiên đến thời điểm hiện tại.

time_ratio = minutes_elapsed / 225 # 225 phút thực giao dịch (loại ATO 15ph + ATC 15ph)

GTGD_kỳ_vọng = GTGD20 × time_ratio

**intraday_ratio = GTGD_intraday / GTGD_kỳ_vọng**

Cập nhật 5 phút/lần

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

**CV = std(GTGD_20_phiên) / mean(GTGD_20_phiên) × 100**

Dùng 20 phiên trước , cập nhật đầu phiên.

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

\+ 0.1 × Điểm tích lũy/phân phối (A/D) ← học từ CANSLIM

\+ 0.15 × Smart Money Flow

\+ 0.1 × Điểm xác nhận kỹ thuật (RSI+MACD)

### Điểm biến động giá đa khung (trọng số 0.3)

_Mã có đang chạy mạnh hơn bình thường không - xét đa khung thời gian để lọc noise?_

| **Khung**   | **Biến**   | **Câu hỏi**                 | **Mục đích**                                       |
| ----------- | ---------- | --------------------------- | -------------------------------------------------- |
| 1D (ngày)   | return_1d  | Hôm nay có tăng không?      | Trigger nhỏ - không để "chasing" kéo điểm          |
| 5D (tuần)   | return_5d  | Tuần qua có momentum không? | Main signal - khớp holding period swing trade      |
| 20D (tháng) | return_20d | Tháng qua uptrend không?    | Trend context - tránh mua trong downtrend phục hồi |

return_1d = (close_hôm_nay - close_1d_trước) / close_1d_trước × 100

return_5d = (close_hôm_nay - close_5d_trước) / close_5d_trước × 100

return_20d = (close_hôm_nay - close_20d_trước) / close_20d_trước × 100

**1\. Component 1 - score_1d (weight 0.15)**

**Câu hỏi:** _"Hôm nay có tăng không?"_

**Logic:**

- Signal 1D có độ nhiễu cao nhất trong 3 timeframe - weight thấp phản ánh mức độ tin cậy thấp hơn.
- Bảng điểm đơn giản, tăng dần: không có extended penalty vì thiếu cơ sở thực nghiệm trên dữ liệu HOSE.
- Assumption "return_1d cao = rủi ro T+2.5" là heuristic chưa được backtest - cần validate trước khi áp dụng penalty.

| **return_1d** | **Điểm** | **Ý nghĩa**                         |
| ------------- | -------- | ----------------------------------- |
| < −1%         | **0**    | Giảm rõ hôm nay - momentum tiêu cực |
| \-1% → 0%     | **20**   | Buffer zone - nhẹ âm                |
| 0% → 1%       | 50       | Nhẹ dương                           |
| 1% → 3%       | **75**   | Momentum tích cực                   |
| \> 3%         | **90**   | Mạnh - chưa có cơ sở penalty        |

**2\. Component 2 - score_5d (weight 0.50) ← Main signal**

**Câu hỏi:** _"Trong 1 tuần qua mã có momentum rõ ràng không - khớp với holding period?"_

**Logic:**

- 5D (~1 tuần) là khung thời gian trung tâm của swing trade. Đây là signal chính.
- Soft cap khi return_5d > 15%: mã tăng quá 15% trong 1 tuần rất có thể đã extended về weekly. Không phạt mạnh (vẫn 65đ) nhưng tránh cho điểm tối đa.
- Pullback nhẹ (−3% → 0%): không phạt quá nặng - pullback về MA20 vẫn là setup đẹp cho breakout tiếp theo.

| **return_5d** | **Điểm** | **Ý nghĩa**                           |
| ------------- | -------- | ------------------------------------- |
| < −3%         | **0**    | Giảm mạnh trong tuần - momentum âm rõ |
| −3% → 0%      | **15**   | Pullback nhẹ - chờ xác nhận           |
| 0% → 2%       | 40       | Flat đến nhẹ lên                      |
| 2% → 5%       | **70**   | Momentum rõ                           |
| 5% → 10%      | **90**   | Mạnh - setup tốt                      |
| 10% → 15%     | **100**  | Rất mạnh - leader rõ ràng             |
| \> 15%        | 65       | Extended weekly - soft cap            |

**3\. Component 3 - score_20d (weight 0.35)**

**Câu hỏi:** _"Trong 1 tháng qua xu hướng có ủng hộ không - tránh mua bounce trong downtrend?"_

**Logic:**

- Weight cần đủ lớn để loại mã đang downtrend tháng nhưng bounce tuần.
- Soft cap khi return_20d > 25% (75đ thay vì 100đ): vẫn uptrend mạnh nhưng rủi ro extended ở monthly frame. Không phạt nặng vì Stage 2 mạnh có thể duy trì.
- Phân biệt với score_ma (3.2.2): return_20d đo velocity/tốc độ tăng trong 1 tháng. price_vs_ma20 đo position/vị trí hiện tại so với trung bình. Hai thứ khác nhau dù có tương quan.

| **return_20d** | **Điểm** | **Ý nghĩa**                                 | **Weinstein Stage** |
| -------------- | -------- | ------------------------------------------- | ------------------- |
| < −5%          | **0**    | Downtrend tháng - tránh tuyệt đối           | Stage 4             |
| −5% → 0%       | **20**   | Tháng yếu - có thể Stage 1 hoặc 4           | Stage 1/4           |
| 0% → 5%        | 50       | Nhẹ lên - Stage 2 sớm hoặc Stage 1 kết thúc | Early Stage 2       |
| 5% → 15%       | **80**   | Uptrend tháng rõ - Stage 2 mid              | Stage 2 healthy     |
| 15% → 25%      | **100**  | Uptrend mạnh - leader tháng                 | Stage 2 strong      |
| \> 25%         | 75       | Vẫn uptrend nhưng hơi quá - soft cap        | Stage 2 extended    |

**4\. Component 4 - Consistency Multiplier**

**Câu hỏi:** _"Cả 3 khung có cùng chiều không - hay đang mâu thuẫn nhau?"_

**Logic:**

- Khi 3 timeframe aligned cùng chiều, xác suất momentum tiếp tục cao hơn nhiều so với mixed signals.
- Implement là multiplier (không phải weight riêng) để tránh inflate tổng weights và giữ công thức gọn.
- Penalty khi 20D tốt nhưng 1D/5D âm: đây là dấu hiệu đảo chiều, không phải setup mua.

| **Số TF dương** | **Multiplier** | **Ý nghĩa**                     | **Ví dụ điển hình**                     |
| --------------- | -------------- | ------------------------------- | --------------------------------------- |
| Cả 3 dương      | **× 1.10**     | Momentum aligned - bonus 10%    | +1% / +6% / +12% → tăng đều mọi khung   |
| 2/3 dương       | × 1.00         | Tín hiệu ổn - không điều chỉnh  | +0.5% / +5% / −2% → tháng pullback nhẹ  |
| 1/3 dương       | × 0.85         | Mixed signals - penalty 15%     | −0.5% / −3% / +18% → đảo chiều ngắn hạn |
| 0/3 âm          | **× 0.70**     | Momentum tiêu cực - penalty 30% | −2% / −5% / −8% → downtrend toàn khung  |

**composite = (0.15 × return_1d + 0.5 × return_5d + 0.35 × return_20d)\* consistency_mult**

**(Nếu giá trị lớn hơn 100 thì cap ở 100)**

### Điểm phân tích MA

Đo \*\*sức khỏe cấu trúc xu hướng\*\* của cổ phiếu thông qua 4 câu hỏi:

| **Câu hỏi**                                             | **Component**       | **Weight** | **Cập nhật** |
| ------------------------------------------------------- | ------------------- | ---------- | ------------ |
| "Entry point có gần MA20 không - stop có chặt không?"   | score_price_vs_ma20 | 0.35       | 5 phút       |
| "Uptrend trung hạn có đang được xác nhận không?"        | score_price_vs_ma50 | 0.20       | EOD          |
| "MA20 đã nằm trên MA50 chưa - Stage 2 đã bắt đầu chưa?" | score_alignment     | 0.20       | EOD          |
| "Momentum có đang tăng tốc không?"                      | score_slope         | 0.25       | EOD          |
| TỔNG                                                    |                     | **1.00 ✓** |              |

**Dữ liệu đầu vào**

| **Biến** | **Định nghĩa**                         | **Cập nhật** | **Ghi chú**                  |
| -------- | -------------------------------------- | ------------ | ---------------------------- |
| ma20     | mean(close, 20 phiên trước)            | EOD          | Không đổi trong ngày         |
| ma50     | mean(close, 50 phiên trước)            | EOD          | Không đổi trong ngày         |
| ma20_10d | MA20 tính đến thời điểm 10 phiên trước | EOD          | Dùng cho slope               |
| ma50_10d | MA50 tính đến thời điểm 10 phiên trước | EOD          | Dùng cho slope               |
| Close    | Giá đóng cửa hiện tại                  | 5 phút       | Intraday - cập nhật liên tục |

**1\. Component 1 - score_price_vs_ma20 (weight 0.35)**

**Câu hỏi:** _"Entry point có gần MA20 không - stop-loss có đủ chặt không?"_

**Logic:**

- Với swing trade T+2.5, điểm vào lý tưởng là khi giá đang tight above MA20 (0-3.5%).
- Giá quá xa MA20 → stop phải đặt xa → R:R xấu đi; nếu bị khóa T+2.5 khi giá pullback về MA20 = lỗ lớn.

**Công thức:**

price_vs_ma20 = (close - ma20) / ma20 × 100 # % so với MA20

| **price_vs_ma20** | **Điểm** | **Ý nghĩa**                               |
| ----------------- | -------- | ----------------------------------------- |
| < −2%             | **0**    | Rõ ràng dưới MA20 - không mua             |
| −2% đến 0%        | **15**   | Buffer zone - just dưới, tín hiệu yếu     |
| 0% đến 1.5%       | **75**   | VCP sweet spot - tight, stop gần, R:R tốt |
| 1.5% đến 3.5%     | **90**   | Tốt - vẫn gần MA20, trong vùng an toàn    |
| 3.5% đến 6%       | 65       | Chấp nhận được - bắt đầu xa dần           |
| 6% đến 9%         | **30**   | Extended - T+2.5 risk rõ rệt              |
| \> 9%             | **0**    | Quá xa - không đuổi giá                   |

**2\. Component 2 - score_price_vs_ma50 (weight 0.20)**

**Câu hỏi:** _"Uptrend trung hạn có đang được xác nhận không?"_

**Logic:**

- MA50 là đường uptrend trung hạn. Khác với MA20, khoảng cách xa hơn so với MA50 vẫn là tín hiệu tốt (uptrend mạnh).
- Không áp dụng extended penalty ở đây - giá 15% trên MA50 là Stage 2 rõ ràng, không phải rủi ro.
- Giá dưới MA50: Weinstein Stage 3 (phân phối) hoặc Stage 4 (downtrend) → 0 điểm.

**Công thức:**

price_vs_ma50 = (close - ma50) / ma50 × 100 # % so với MA50

| **price_vs_ma50** | **Điểm** | **Ý nghĩa**                           |
| ----------------- | -------- | ------------------------------------- |
| < −2%             | **0**    | Dưới MA50 xa - không mua              |
| −2% đến 0%        | **15**   | Buffer zone - just dưới MA50          |
| 0% đến 3%         | 50       | Vừa vượt MA50 - recovery, chưa chắc   |
| 3% đến 8%         | **80**   | Uptrend trung hạn rõ ràng             |
| 8% đến 15%        | **100**  | Stage 2 khỏe - uptrend xác nhận       |
| \> 15%            | 70       | Rất xa MA50, vẫn uptrend nhưng hơi xa |

**3\. Component 3 - score_alignment (weight 0.20) ← Bổ sung mới**

**Component hoàn toàn mới** - Không có trong spec RevB

**Câu hỏi:** _"MA20 đã nằm trên MA50 chưa - Weinstein Stage 2 đã bắt đầu chưa?"_

**Vấn đề với spec cũ:**

- Spec cũ tính price_vs_ma20 và price_vs_ma50 độc lập nhau, không nắm bắt được mối quan hệ giữa hai đường MA.
- Kết quả: Stage 2 uptrend thật và dead cat bounce có thể cho điểm MA y hệt nhau.

| **Kịch bản**        | **Mô tả**                 | **RevB (cũ)**       | **RevC (mới)**              |
| ------------------- | ------------------------- | ------------------- | --------------------------- |
| **Stage 2 uptrend** | price > MA20, MA20 > MA50 | ~72 điểm            | **score_alignment = 100 ✓** |
| **Dead cat bounce** | price > MA20, MA20 < MA50 | **~72 điểm ← BẪY!** | **score_alignment = 0 ✓**   |

**Công thức:**

ma20_vs_ma50 = (ma20 - ma50) / ma50 × 100 # % MA20 so với MA50

| **ma20_vs_ma50** | **Điểm** | **Ý nghĩa**                              |
| ---------------- | -------- | ---------------------------------------- |
| < −3%            | **0**    | MA20 dưới MA50 xa - cấu trúc downtrend   |
| −3% đến −1%      | **20**   | Bearish alignment - MA20 dưới MA50       |
| −1% đến 0%       | 40       | Sắp cross - chờ xác nhận golden cross    |
| 0% đến 1%        | 65       | MA20 vừa vượt MA50 - golden cross sớm    |
| 1% đến 3%        | **85**   | Alignment tốt - Stage 2 đang hình thành  |
| \> 3%            | **100**  | Stage 2 uptrend rõ ràng - alignment mạnh |

**4\. Component 4 - score_slope (composite) (weight 0.25)**

**Câu hỏi:** _"Cả xu hướng ngắn hạn VÀ trung hạn có đang tăng tốc không?"_

**Cải tiến so với spec cũ:**

- Lookback: 5 phiên → 10 phiên (giảm noise đáng kể).
- Coverage: MA20 only → MA20 (×0.55) + MA50 (×0.45). MA50 slope bắt đầu dốc lên sau tích lũy = tín hiệu tổ chức mua trung hạn rất quan trọng.

**Công thức:**

\# Slope MA20 - momentum ngắn hạn

slope_ma20 = (ma20 - ma20_10d) / ma20_10d × 100 # % thay đổi 10 phiên

\# Slope MA50 - xác nhận tổ chức đang tích lũy

slope_ma50 = (ma50 - ma50_10d) / ma50_10d × 100 # % thay đổi 10 phiên

\# Composite - ưu tiên MA20 (ngắn hạn) nhưng MA50 xác nhận

score_slope = 0.55 × score_slope_ma20 + 0.45 × score_slope_ma50

| **slope_ma20 (10 phiên)** | **Điểm** | **Ý nghĩa**                         |
| ------------------------- | -------- | ----------------------------------- |
| < −0.3%                   | **0**    | MA20 đang dốc xuống - tránh         |
| −0.3% đến 0%              | **15**   | Flattening - momentum đang chết đi  |
| 0% đến 0.3%               | 40       | Phẳng đến nhẹ lên                   |
| 0.3% đến 0.6%             | 70       | Upslope rõ - momentum đang xây dựng |
| \> 0.6%                   | **100**  | Upslope mạnh - tăng tốc rõ ràng     |

| **slope_ma50 (10 phiên)** | **Điểm** | **Ý nghĩa**                               |
| ------------------------- | -------- | ----------------------------------------- |
| < −0.2%                   | **0**    | MA50 đang dốc xuống - downtrend trung hạn |
| −0.2% đến 0%              | **20**   | Flattening - bắt đầu ổn định              |
| 0% đến 0.2%               | 50       | Nhẹ lên - recovery                        |
| 0.2% đến 0.4%             | **80**   | Upslope tốt - tổ chức đang mua dần        |
| \> 0.4%                   | **100**  | Mạnh - uptrend trung hạn đang xác nhận    |

**5\. Công thức tổng hợp - score_ma**

score_ma = 0.35 × score_price_vs_ma20 # vị trí entry vs support ngắn hạn

\+ 0.20 × score_price_vs_ma50 # xác nhận uptrend trung hạn

\+ 0.20 × score_alignment # MA20 vs MA50 - Stage 2 check

\+ 0.25 × score_slope # momentum acceleration

**Tần suất cập nhật**

| **Component**       | **Cập nhật** | **Lý do**                        |
| ------------------- | ------------ | -------------------------------- |
| score_price_vs_ma20 | 5 phút / lần | close intraday thay đổi liên tục |
| score_price_vs_ma50 | 5 phút / lần | close intraday thay đổi liên tục |
| score_alignment     | EOD (1 lần)  | ma20, ma50 không đổi trong ngày  |
| score_slope         | EOD (1 lần)  | slope_ma20, slope_ma50 không đổi |

### Điểm sức mạnh tương đối vs VN-Index

_Tham khảo từ: VCP - Relative Strength component (15% weight trong VCP)_

_Phương pháp VCP phát hiện rằng các "leading stock" luôn outperform index trước khi breakout. Mã breakout nhưng tăng ít hơn VN-Index trong 3 tháng = không phải leader, xác suất thành công thấp hơn. Với lướt sóng, chỉ chơi mã đang dẫn dắt thị trường._

_\# Ưu tiên 3 tháng gần nhất cho lướt sóng (VCP dùng 12 tháng cho swing dài hơn)_

**1\. Công thức tổng hợp**

| **Bước**                  | **Công thức**                                   | **Ghi chú**                                                                                                                                                                                                                                                                                                                                                                  |
| ------------------------- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1\. Excess return 1 tháng | rs_1m = stock_return_1M − vnindex_return_1M     | 21 phiên giao dịch                                                                                                                                                                                                                                                                                                                                                           |
| 2\. Excess return 3 tháng | rs_3m = stock_return_3M − vnindex_return_3M     | stock_return_3M = % thay đổi giá của cổ phiếu trong 3 tháng gần nhất.<br><br>stock_return_3M = (close_today - close_63d_ago) / close_63d_ago × 100<br><br>(63 phiên giao dịch ≈ 3 tháng (21 phiên/tháng × 3)<br><br>\`\`\`<br><br>vnindex_return_3M = (vnindex_close_today - vnindex_close_63d_ago) / vnindex_close_63d_ago × 100<br><br>close_today: giá khớp lệnh mới nhất |
| 3\. Composite             | rs_weighted = 0.35 × rs_3m + 0.65 × rs_1m       | 1M weight cao hơn: cần leader đang nổi ngay bây giờ                                                                                                                                                                                                                                                                                                                          |
| 4\. Acceleration          | rs_acceleration = rs_1m − rs_3m                 | Dương = RS đang tăng tốc                                                                                                                                                                                                                                                                                                                                                     |
| 5\. Final score           | score_rs = min(100, score_rs_base × accel_mult) |                                                                                                                                                                                                                                                                                                                                                                              |

**2\. Bảng điểm rs_weighted**

| **rs_weighted** | **Điểm** | **Ý nghĩa**                        |
| --------------- | -------- | ---------------------------------- |
| \> +15%         | **100**  | Superleader - outperform vượt trội |
| +8% → +15%      | **85**   | Leader rõ ràng                     |
| +3% → +8%       | **65**   | Outperform tốt                     |
| 0% → +3%        | 45       | Nhỉnh hơn index nhẹ                |
| −5% → 0%        | 20       | Underperform nhẹ                   |
| < −5%           | **0**    | Underperform rõ - không ưu tiên    |

**3\. Bảng RS Acceleration Multiplier**

| **rs_1m − rs_3m** | **Multiplier** | **Ý nghĩa**                                     |
| ----------------- | -------------- | ----------------------------------------------- |
| \> +5%            | **× 1.10**     | RS tăng tốc mạnh - emerging leader đang nổi lên |
| 0% → +5%          | × 1.00         | RS bình thường                                  |
| −5% → 0%          | × 0.90         | RS đang chậm lại - cảnh báo                     |
| < −5%             | **× 0.80**     | Ex-leader - RS mất sức rõ ràng                  |

#### Điểm tích lũy/phân phối (A/D Ratio)

_Tham khảo từ: CANSLIM - S component (Supply & Demand, 15% weight). CANSLIM S component phát hiện smart money đang mua hay bán. Nếu volume ngày tăng giá > volume ngày giảm giá → tổ chức đang tích lũy → momentum có nền tảng. Đây là tín hiệu SỚM hơn breakout, giúp phân biệt breakout có dòng tiền thật hay không._

_20 phiên gần nhất (điều chỉnh từ 60 phiên của CANSLIM - phù hợp lướt sóng ngắn hạn hơn)_

up_days_vol = \[volume\[i\] for i in range(20) if close\[i\] > close\[i-1\]\]

down_days_vol = \[volume\[i\] for i in range(20) if close\[i\] < close\[i-1\]\]

ad_ratio = mean(up_days_vol) / mean(down_days_vol)

| **A/D ratio** | **Điểm** | **Ý nghĩa**                                                   |
| ------------- | -------- | ------------------------------------------------------------- |
| ≥ 2.0         | 100      | Tích lũy mạnh (smart money vào)                               |
| 1.5-2.0       | 80       | Tích lũy rõ ràng                                              |
| 1.0-1.5       | 60       | Trung tính / tích lũy nhẹ                                     |
| 0.7-1.0       | 40       | Phân phối nhẹ                                                 |
| < 0.7         | 20       | Phân phối rõ (smart money ra)                                 |
| ∞             | 100      | Cả 20 phiên tăng giá -> mean(down_days_vol) = 0 → chia cho 0. |

### Điểm Smart Money Flow

**\# --- Net Foreign Flow --- (Khối ngoại)**

foreign_net_5d = sum(foreign_buy_value - foreign_sell_value, 5_phiên) # VND

foreign_buy_value: khối ngoại mua bao nhiêu tiền trong ngày

foreign_sell_value: khối ngoại bán bao nhiêu tiền trong ngày

foreign_buy_value - foreign_sell_value: mua ròng của từng ngày

foreign_net_5d : Cộng 5 ngày gần nhất lại → tổng dòng tiền ròng khối ngoại trong 1 tuần

**foreign_net_pct = foreign_net_5d / sum(GTGD thực tế 5 phiên) × 100**: Chuẩn hóa theo quy mô giao dịch để tính tỉ lệ tương đối % sẽ chính xác hơn là lấy giá trị tuyệt đối do tỉ lệ mua ròng lớn hay nhỏ không chỉ phụ thuộc vào giá trị tuyệt đối mà còn phụ thuộc vào mã. Ví dụ HPG giao dịch 500 tỷ/ngày → 90 tỷ chỉ chiếm tỷ lệ nhỏ nhưng một mã mid-cap giao dịch 30 tỷ/ngày → 90 tỷ là rất lớn

| Foreign net % (5d) | Điểm | Ý nghĩa                      |
| ------------------ | ---- | ---------------------------- |
| \> +5%             | 100  | Khối ngoại mua ròng rất mạnh |
| +2% đến +5%        | 80   | Mua ròng rõ ràng             |
| +0.5% đến +2%      | 60   | Mua ròng nhẹ                 |
| \-0.5% đến +0.5%   | 40   | Trung tính                   |
| \-2% đến -0.5%     | 20   | Bán ròng nhẹ                 |
| < -2%              | 0    | Bán ròng mạnh - cảnh báo     |

**\# --- Net Proprietary Flow --- (Tự doanh)**

prop_net_5d = sum(prop_buy_value - prop_sell_value, 5_phiên) # VND

prop_net_pct = prop_net_5d / sum(GTGD thực tế 5 phiên) × 100

| Prop net % (5d)  | Điểm | Ý nghĩa                |
| ---------------- | ---- | ---------------------- |
| \> +3%           | 100  | Tự doanh tích lũy mạnh |
| +1% đến +3%      | 80   | Mua ròng rõ            |
| +0.3% đến +1%    | 60   | Mua ròng nhẹ           |
| \-0.3% đến +0.3% | 40   | Trung tính             |
| \-1% đến -0.3%   | 20   | Bán ròng nhẹ           |
| < -1%            | 0    | Bán ròng mạnh          |

Lưu ý: Ngưỡng proprietary thấp hơn foreign vì tự doanh thường giao dịch khối lượng nhỏ hơn so với quỹ ngoại.

**\# --- Composite Smart Money Score ---**

smart_money_score = 0.60 × score(foreign_net_pct) + 0.40 × score(prop_net_pct)

> **Lưu ý về dữ liệu (granularity):** Giá trị mua/bán (buy/sell **value**) của khối ngoại và tự doanh từ `vnstock_data` chỉ có ở mức **cuối phiên (end-of-day, per-session)** — không có dữ liệu intraday/realtime. `intraday()` chỉ trả `time/price/volume`; `price_board()` realtime chỉ có foreign buy/sell **volume** (không có value, không có tự doanh). Do đó component Smart Money Flow **không cập nhật trong phiên**: dù app refresh 5 phút/lần, giá trị này giữ nguyên theo phiên T-1 cho tới khi phiên mới chốt.

### Điểm xác nhận kỹ thuật score_technical (RSI + MACD)

#### RSI 14 phiên

| **RSI (14 phiên)** | **Điểm** | **Ghi chú**                                           |
| ------------------ | -------- | ----------------------------------------------------- |
| < 40               | 0        | Quá yếu                                               |
| 40-50              | 20       | Yếu                                                   |
| 50-60              | 60       | Momentum đang xây                                     |
| **60-70**          | **100**  | **Sweet spot cho swing - mạnh nhưng còn room tăng**   |
| 70-80              | 60       | Rủi ro mean-reversion trong 2.5 phiên                 |
| \> 80              | 20       | Nguy hiểm - khả năng đảo chiều trước khi bạn bán được |

_(Logic: Với T+2.5, điểm tối ưu là momentum đang tăng nhưng chưa quá nóng - RSI 60-70 cho xác suất tiếp tục tốt nhất trong 3-5 phiên tiếp theo.)_

#### MACD - chuẩn hóa theo giá

histogram = macd_line - signal_line

histogram_pct = histogram / close_today × 100

| **Histogram%** | **Điểm** |
| -------------- | -------- |
| < 0%           | 20       |
| 0-0.05%        | 50       |
| \> 0.05%       | 100      |

**score_technical = 0.60 × score(RSI) + 0.40 × score(MACD)**

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

\+ 0.10 × Điểm sức mạnh đóng cửa (closing_strength)

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

### Điểm sức mạnh đóng cửa (closing_strength)

|     |     |
| --- | --- |
|     |     |
|     |     |
|     |     |
|     |     |
|     |     |

**closing_strength = (close - low) / (high - low) × 100**

| Closing strength | Điểm | Ý nghĩa                                             |
| ---------------- | ---- | --------------------------------------------------- |
| \> 80%           | 100  | Đóng cửa gần high - buyers kiểm soát đến cuối phiên |
| 60-80%           | 80   | Khá tốt                                             |
| 40-60%           | 60   | Trung tính                                          |
| 20-40%           | 40   | Yếu                                                 |
| < 20%            | 20   | Đóng cửa gần low - sellers kiểm soát cuối phiên     |

_(Lý do: Closing strength phản ánh ai kiểm soát cuối phiên - dự báo tốt hơn cho gap mở cửa ngày mai và xu hướng các phiên tiếp theo. Data chỉ cần OHLC (đã có sẵn).)_

### Hệ số đánh giá rủi ro bị khóa T+2.5 (risk_ratio)

\# Rủi ro bị khóa = breakout đã chạy xa + biên độ dao động lớn

**risk_ratio = breakout_ratio × (atr_5d / close × 100)**

ATR đo biên độ dao động trung bình mỗi phiên - mã này mỗi ngày giá nhảy bao nhiêu? Do thị trường VN bị khóa tối thiểu 2.5 phiên, ATR cho biết giá có thể chạy ngược bao xa trước khi bán được. Đây là một technical indicator có sẵn.

True Range (1 phiên) = max trong 3 giá trị sau:

1\. high - low (biên độ trong phiên)

2\. |high - close_hôm_trước| (gap lên)

3\. |low - close_hôm_trước| (gap xuống)

ATR_5d = mean(True Range, 5 phiên gần nhất)

| Risk ratio | Hệ số  | Ý nghĩa                                  |
| ---------- | ------ | ---------------------------------------- |
| < 3        | × 1.0  | Breakout gần + ổn định → giữ nguyên điểm |
| 3-5        | × 0.85 | Rủi ro vừa → giảm nhẹ 15%                |
| 5-7        | × 0.70 | Rủi ro cao → giảm 30%                    |
| \> 7       | × 0.50 | Rất nguy hiểm → giảm 50% điểm breakout   |

**breakout_score_final = breakout_score_raw × risk_ratio**

| Thành phần           | Đo cái gì                          | Ví dụ                 |
| -------------------- | ---------------------------------- | --------------------- |
| breakout_ratio       | Giá đã chạy xa High20 bao nhiêu    | 1.03 = đã vượt 3%     |
| atr_5d / close × 100 | Biên độ dao động %/ngày            | 4% = mỗi ngày nhảy 4% |
| risk_ratio           | Kết hợp: xa + volatile = nguy hiểm | 1.03 × 4 = 4.12       |

## Tần suất chạy các tham số

| Metric                       | Tính lại mỗi 5 phút? | Lý do                                     |
| ---------------------------- | -------------------- | ----------------------------------------- |
| GTGD20                       | Không                | Data 20 phiên trước, không đổi trong ngày |
| Safety ratio                 | Không                | GTGD20 không đổi, position_size không đổi |
| CV                           | Không                | Dùng 20 phiên trước                       |
| MA20, MA50                   | Không                | Dùng close 20/50 phiên trước              |
| RS vs VN-Index               | Không                | Dùng close 1M/3M trước                    |
| A/D Ratio                    | Không                | 20 phiên trước                            |
| Volume dry-up                | Không                | 4 phiên trước                             |
| Base quality (ATR)           | Không                | 5/20 phiên trước                          |
|                              |                      |                                           |
| Intraday activity            | Có                   | Volume + giá thay đổi liên tục            |
| Breakout ratio               | Có                   | close hiện tại thay đổi                   |
| Volume breakout confirmation | Có                   | Volume intraday tăng dần                  |
| Closing strength             | Có                   | OHLC intraday thay đổi                    |
| RSI, MACD                    | Có                   | Giá hiện tại ảnh hưởng phiên đang chạy    |
| Return 1D                    | Có                   | Giá hiện tại thay đổi                     |
| Risk ratio                   | Có                   | Breakout ratio + ATR intraday             |
| Smart Money Flow             | Có                   | Nếu data foreign/prop cập nhật realtime   |