# website/utils.py
def convert_currency_to_int(currency_str):
    if isinstance(currency_str, (int, float)):
        return int(currency_str)
    try:
        # Loại bỏ ký hiệu $, dấu chấm và khoảng trắng
        cleaned_str = currency_str.replace("$", "").replace(".", "").strip()
        # Kiểm tra xem chuỗi có phải là số hợp lệ không
        if not cleaned_str.isdigit():
            raise ValueError("Chuỗi sau khi xử lý không phải là số hợp lệ.")
        return int(cleaned_str)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Không thể chuyển đổi '{currency_str}' thành số: {str(e)}")

def convert_int_to_currency(number):
    if not isinstance(number, (int, float)):
        raise ValueError(f"Đầu vào phải là số, nhận được: {type(number)}")
    # Chuyển số thành chuỗi và định dạng với dấu chấm phân cách hàng nghìn
    number_str = str(int(number))
    currency_str = ""
    count = 0
    for digit in reversed(number_str):
        if count != 0 and count % 3 == 0:
            currency_str = "." + currency_str
        currency_str = digit + currency_str
        count += 1
    currency_str = "$" + currency_str
    return currency_str