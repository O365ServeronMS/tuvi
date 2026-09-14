---
id: npl#0010-cach-tinh-tong-so-doi-da-la-so-tu-vi
book: nguyen-phat-loc
book_code: npl
book_title: "Tử Vi Tổng Hợp (Nguyễn Phát Lộc)"
title: "Cách tính tổng số đối đa lá số Tử-Vi"
heading_path:
  - "Chương này có dành một phụ lục để dẫn giải bài toán tính tổng số tối đa lá số Tử-Vi. Độc"
  - "Cách tính tổng số đối đa lá số Tử-Vi"
level: 2
ordinal: 10
part: 1
parts: 1
source_file: input/TU-VI-TONG-HOP-NGUYEN-PHAT-LOC.clean.md
source_lines: 468-591
chars: 7357
stars_detected: [da-la, tu-vi]
stars_in_title: [da-la, tu-vi]
palaces_detected: [than]
non_luan: true
---

## Cách tính tổng số đối đa lá số Tử-Vi

Để tính tổng số tối đa lá số Tử-Vi có thể có, ta tiến hành theo 3 bước dưới đây: Nếu dữ kiện, trong đó liệt kê các yếu tố can dự vào việc tính, giải thích các yếu tố này.

Nêu nguyên tắc tính.

Trình bày kỹ thuật tính. a) Những dữ kiện

Khi tính tổng số lá số Tử-Vi, ta phải căn cứ vào 5 yếu tố:

Yếu tố Âm Dương, yếu tố giờ sinh, yếu tố tháng sinh, yếu tố năm sinh, yếu tố ngày sinh trong tháng

Yếu tố Âm Dương – có hai loại tuổi, tuổi Dương (Dương, Nam, Dương Nư) và tuổi Âm (Âm Nam, Âm Nữ), tương ứng với cũng hướng an sao, một hướng thuận và một hướng nghịch.

Yếu tố giờ sinh - Âm lịch có 12 giờ trong ngày. Yếu tố tháng sinh – Năm thường có 12 tháng, riêng năm nhuận có mười 13 tháng. Những tháng

nhuận ta không kể vì lá số Tử-Vi cứ an theo tháng, bất luận tháng thường hay tháng nhuận. Do đó, ta chỉ kể một năm có 12 tháng mà thôi. Có tháng thiếu gồm 29 ngày, có tháng đủ gồm 30 ngày. Sự nối tiếp các tháng thiếu và đủ

trong một năm không theo thứ tự nào cả, tức là không phải cứ nhất thiết một tháng đủ đi tiếp theo một tháng thuế. Ta có nhiều dịp chứng kiến 2 hoặc có khi 3 tháng thiếu đi liền nhau, rồi cũng không phải là 2 hoặc 3 tháng đủ đi theo sát.

Về tỷ lệ tháng đủ, tháng thiếu cũng không đồng nhất trong các năm. Có năm có 7 tháng đủ, 5 tháng thiếu, có năm thì tỷ lệ bằng nhau 6/6. cũng không hẳn một năm gặp tỷ lệ 6/6 di sát theo một năm có tỷ lệ 7/5: có khi tỷ lệ 6/6 xảy ra trong 2 năm liền, có khi tỷ lệ 7/5 có trong 4 năm liền.

Những nét đặc thù kể trên khiến cho việc tính ngày trong năm phải dùng cách đếm. Năm nào có tỷ lệ 7/5 thì có ngày 355 ngày đểlấy số, còn năm có tỷ lệ 6/6 thì có 354 ngày.

Yếu tố năm sinh – Năm sinh bao gồm can và chi. Có 10 can và 12 chi, được kết hợp với nhau theo một quy tắc rất đặc thù. Không phải can nào cũng có thể đi với bất cứ chi nào. Quy luật chắp nối 10 can với 12 chi chỉ đưa tới 60 thế kết hợp là hết ** chớ không phải đưa tới 10 x 12 tức 120 kết hợp như nhiều người lầm tưởng. 60 loại 6 của con người, nối tiếp nhau trong 60 năm. Đến năm thứ 61 (1900) thì trở lại Canh Tý, khởi đầu cho một giáp kế tiếp. Khởi điểm của giáp có thể lấy ở bất cứ

năm nào. Ví dụ, có thể lấy Bính Thìn (1càng làm năm đầu tiên cho giáp Bính Thìn Aát Mão (1796 – 1855). Sau năm Aát Mão (1855) thì trở lại Bính Thìn (1856)

vậy: mỗi can chi có 6 thể hết hợp với 6 chi. Thành thử 10 can chỉ có 60 thể kết hợp với 12 chi.

Trong bất luận giáp nào, tên gọi các năm và thứ tự kết hợp can chi của năm trong giáp

không bao giờ thay đổi. Ví dụ sau Bính Thìn thì đến Đinh Tý, rồi đến Mậu Ngọ, Kỹ Mùi, … cho đến năm thứ 60 của giáp là Aát Mão. Luôn luôn như vậy.

Tóm lại, vì những đặc điểm trên, cho nên, trong một gíap, chỉ có 60 loại tuổi để lấy số Tử- Vi cho loài người mà thôi, không hơn không kém. Vấn đề đặt cho ta là tìm trong 60 năm này số lượng ngày để tính tổng số lá số Tử-Vi, lấy theo ngày.

Yếu tố ngày sinh - Ta có thể tìm số ngày trung bình torng tháng để nhân với số tháng trong năm, với số năm trong giáp, với số giờ trong ngày và với hệ số âm dương ngõ hầu đi đến tích số chung, tức là tổng số lá số Tử-Vi khả hữu.

Ta cũng có thể áp dụng một bài toán giản dị hoưn là tìm số ngày trong giáp (trong đó có bao gồm cả 60 năm và số tháng rồi) để nhân với số giáp trong ng2y và với hệ số Âm Dương.

b) Nguyên tắc tính tổng số lá số Tử-Vi trong giáp

Có hai cách tính tổng số: Cách tính bằng 5 hệ số và cách tính với 3 hệ số. Với cách tính bằng 5 hệ số, tổng số lá số tất cả trong giáp (gọi là y) là tích số của 5 hệ số sau đây:

Hệ số Âm Dương : 2

Hệ số giờ trong ngày : 1 Hệ số trung bình trong tháng : x*

Hệ số tháng trong năm : 12

Hệ số năm trong giáp : 60 Phương trình sẽ là : y = 12 X 12 X x X 12 X 60

Còn cách tính bằng 3 hệ số sẽ giản dị hơn. Tổng số lá số Tử-Vi trong giáp (y) là tích số của 3 hệ số sau:

Hệ số Âm Dương : 2 Hệ số giờ trong ngày : 12

Hệ số ngày trong giáp : z

Phương trình sẽ là : y = 2 X 12 X z

Sở dĩ theo cách tính này, hệ số tháng và năm không được kể là vì số ngày trong giáp đã được tính dựa theo số tháng năm trong năm (12) và số năm trong giáp (60) rồi. Kỹ thuật trình bày dưới đây sẽ theo cách tính thứ nhì, bằng 3 hệ số cho dễ. Vậy, vấn đề là phải tìm z số ngày trong

giáp.

c) Kỹ thuật tính y trong một giáp nhất định Ta thử chọn một giáp nhất định để tính y, ví dụ như lấy giáp Canh Tý - Kỷ Hợi (1840 –

1899) làm căn bản. Giáp này có 60 năm, trong đó có hai loại năm:

- Loại một gồm 33 năm, mỗi năm có 7 tháng 30 ngày và 5 tháng 29 ngày.

- Loại hai gồm 27 năm, mỗi năm có 6 tháng 30 ngày và 6 tháng 29 ngày. Đối với loại đầu (7 tháng đủ, 5 tháng thiếu), ta có 355 ngày mỗi năm để lấy số Tử-Vi *.

Loại này có 33 năm, vậy trong 33 năm này có 11.715 ngày để lấy số. Đối với loại nhì (6 tháng đủ, 6 tháng thiếu), ta có 354 ngày mỗi năm để lấy số Tử-Vi*. Loại này có 27 năm, vậy, trong 27 năm này có 9.558 ngày để lấy số.

Kết quả là trong trọn giáp 60 năm, ta có:

11.750 + 9.558 = 21.278 ngày để lấy số đó là trị số chính xác của z.

vậy trị số chính xác của y là:

y = 2 X 12 X 21.273 = 510.552 lá số Tử-Vi Tóm lại, trong giáp nói trên, có tất cả 510.552 lá số Tử-Vi. Nói như thế có nghĩa là tất cả

mọi người trrên thế giới sinh trong hoảng thời gian của giáp, kể từ giờ Tý ngày mồng một tháng giêng năm Canh Tý (1840) đến giờ Hợi ngày 30 tháng chạp năm Kỷ Hợi (1899) chỉ có 510.552 vận mệnh mà thôi.

Đó là tổng số lá số Tử-Vi cho riêng giáp 1840 – 1899. Vấn đề đặt ra là đối với cá giáp thì y là bao nhiêu? Làm sao tổng hoá được cho tất cả các giáp?

d) Thử tổng quát hoá tổng số lá số khả hữu

Kết quả 510.552 kể trên đặc biệt chỉ áp dụng riêng cho giáp 1840 – 1899 mà thôi. Ta không thể tổng quát hoá kết quả noí trên cho mọi giáp. Lý do giản dị là vì số ngày z trng giáp này chưa hẳn là số ngày tối đa nếu so với những giáp khác.

Ý niệm của chúng ta là, nếu biết được số ngày tối đa của một

27 năm X 354 ngày = 9.558 ngày Giáp thì mới tổng hoá được, tức là mới biết được tổng số tối đa là số Tử-Vi khả hữu.

Để tìm tổng số tối đa này, ta giả thiết rằng có một giáp giả tưởng nào đó có số ngày cao nhất. Dĩ nhiên, ta không thể giả tưởng quá cao mà phải giả tưởng sao cho càng gần thực tế càng hay. Ta nhận thấy rằng, trong các năm có năm duy nhất có số ngày cao nhất: đó là năm 1944 Giáp

Thân. Năm này có đến 8 tháng 30 ngày và 4 tháng 29 ngày, vị chi là 365 ngày để lấy số. Ta giả thiết rằng gỉ tưởng chỉ gồm toàn những năm 356 ngày thì giáp giả tưởng đó sẽ có:

365 ngày x 60 năm = 21.360 ngày vậy, trị số y bây giờ là:

y = 21.360 x 22 x 12 = 512.640 lá số

Đó là tổng số lá số Tử-Vi tối đa khả chấp*

* * *

# Chương hai

## Phương pháp của khoa Tử-Vi

## Phương pháp phân tích

## • Đại phân tích

## • Vi phân tích

## • Phương pháp động

Con người và đời người là hai đối tượng vô cùng phong phú và phức tạp. Con người là cả một vũ trụ thu hẹp, rắc rối trong sự cấu tạo. Đời người còn khó hiểu hơn, vì nó bao hàm rất nhiều hoàn cảnh khác nhau, nhiều giai đoạn khác nhau mà thời gian có thể phủ trùm gần 100 năm. Con người không bao giờ cố định, đời người cũng thay đổi. Cả hai cùng là biến số của nhau và là biến

số của hoàn cảnh. Vì muốn biết cả hai đối tượng, khoa Tử-Vi hết sức tham vọng. Khoa Tử-Vi giải quyết tham vọng đó như thế nào? Đặt vấn đề như thế tức là noó đến

phương pháp của khoa Tử-Vi. Khoa này áp dụng đồng thời ba phương pháp, phân tích, tổng hợp và động (analytique et dynamique).
