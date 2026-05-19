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

return_1d = (close_hôm_nay - close_1d_trước) / close_1d_trước × 100

return_5d = (close_hôm_nay - close_5d_trước) / close_5d_trước × 100

return_20d = (close_hôm_nay - close_20d_trước) / close_20d_trước × 100

**composite = 0.25 × return_1d + 0.45 × return_5d + 0.30 × return_20d**

_(Trọng số 25/45/30: 5D (~1 tuần) khớp với holding period swing. 20D xác nhận nền momentum. 1D chỉ là trigger nhỏ.)_

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

rs_weighted = 0.35 × rs_3m + 0.65 × rs_1m

_(Lý do: Swing trade cần mã đang dẫn dắt ngay bây giờ, không phải 3 tháng trước. 1M weight cao hơn bắt được rotation sớm hơn.)_

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

### Điểm Smart Money Flow

**\# --- Net Foreign Flow --- (Khối ngoại)**

foreign_net_5d = sum(foreign_buy_value - foreign_sell_value, 5_phiên) # VND

foreign_buy_value: khối ngoại mua bao nhiêu tiền trong ngày

foreign_sell_value: khối ngoại bán bao nhiêu tiền trong ngày

foreign_buy_value - foreign_sell_value: mua ròng của từng ngày

foreign_net_5d : Cộng 5 ngày gần nhất lại → tổng dòng tiền ròng khối ngoại trong 1 tuần

**foreign_net_pct = foreign_net_5d / (GTGD20 × 5) × 100**: Chuẩn hóa theo quy mô giao dịch để tính tỉ lệ tương đối % sẽ chính xác hơn là lấy giá trị tuyệt đối do tỉ lệ mua ròng lớn hay nhỏ không chỉ phụ thuộc vào giá trị tuyệt đối mà còn phụ thuộc vào mã. Ví dụ HPG giao dịch 500 tỷ/ngày → 90 tỷ chỉ chiếm tỷ lệ nhỏ nhưng một mã mid-cap giao dịch 30 tỷ/ngày → 90 tỷ là rất lớn

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

prop_net_pct = prop_net_5d / (GTGD20 × 5) × 100

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

| Thành phần           | Đo cái gì                          | Ví dụ                 |
| -------------------- | ---------------------------------- | --------------------- |
| breakout_ratio       | Giá đã chạy xa High20 bao nhiêu    | 1.03 = đã vượt 3%     |
| atr_5d / close × 100 | Biên độ dao động %/ngày            | 4% = mỗi ngày nhảy 4% |
| risk_ratio           | Kết hợp: xa + volatile = nguy hiểm | 1.03 × 4 = 4.12       |

**breakout_score_final = breakout_score_raw × risk_coefficient**

| Risk ratio | Hệ số  | Ý nghĩa                                      |
| ---------- | ------ | -------------------------------------------- |
| < 3        | × 1.0  | Breakout gần + ổn định → giữ nguyên điểm    |
| 3–5        | × 0.85 | Rủi ro vừa → giảm nhẹ 15%                   |
| 5–7        | × 0.70 | Rủi ro cao → giảm 30%                        |
| > 7        | × 0.50 | Rất nguy hiểm → giảm 50% điểm breakout      |

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