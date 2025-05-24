"""
This file aims to process the input passwords to the rule as follows for convience to train:
    
    pattern <SEP> password

"""

"""
File này được viết để xử lý các mật khẩu đầu vào theo quy tắc sau cho thuận tiện cho việc huấn luyện:
    pattern <SEP> password
"""


import argparse


def get_pattern(password:str):
    """
    Hàm này nhận vào một mật khẩu và trả về một danh sách các chuỗi mô tả kiểu ký tự của mật khẩu.
    Hàm này phân tích mật khẩu thành các phần tử dựa trên loại ký tự (chữ cái, số hoặc ký tự đặc biệt) và độ dài của mỗi phần tử.
    Mỗi phần tử trong danh sách được định dạng dưới dạng "L" cho chữ cái, "N" cho số và "S" cho ký tự đặc biệt, theo sau là độ dài của phần tử đó.
    Ví dụ: nếu mật khẩu là "abc123!@#", hàm sẽ trả về ['L3', 'N3', 'S4'].
    
    :param password: mật khẩu cần phân tích
    :return: danh sách các chuỗi mô tả kiểu ký tự của mật khẩu
    
    
    """
    result = [] # danh sách để lưu trữ các phần tử mô tả kiểu ký tự
    
    current_type = None # biến để theo dõi loại ký tự hiện tại (L, N hoặc S)
    current_length = 0 # biến để theo dõi độ dài của phần tử hiện tại
    
    for char in password: # lặp qua từng ký tự trong mật khẩu
        if char.isalpha(): # kiểm tra xem ký tự có phải là chữ cái hay không
            if current_type == 'L': # nếu loại ký tự hiện tại là chữ cái
                current_length += 1 # tăng độ dài của phần tử hiện tại
            else: # nếu loại ký tự hiện tại không phải là chữ cái
                if current_type: # nếu có loại ký tự hiện tại
                    result.append(current_type + str(current_length)) # thêm phần tử hiện tại vào danh sách kết quả
                current_type = 'L' # cập nhật loại ký tự hiện tại thành chữ cái
                current_length = 1 # đặt độ dài của phần tử hiện tại thành 1
        elif char.isdigit(): # kiểm tra xem ký tự có phải là số hay không
            if current_type == 'N': # nếu loại ký tự hiện tại là số
                current_length += 1 # tăng độ dài của phần tử hiện tại
            else:
                if current_type: # nếu có loại ký tự hiện tại
                    result.append(current_type + str(current_length)) # thêm phần tử hiện tại vào danh sách kết quả
                current_type = 'N' # cập nhật loại ký tự hiện tại thành số
                current_length = 1 # đặt độ dài của phần tử hiện tại thành 1
        else:  # nếu ký tự không phải là chữ cái hoặc số, tức là ký tự đặc biệt
            if current_type == 'S': # nếu loại ký tự hiện tại là ký tự đặc biệt
                current_length += 1 # tăng độ dài của phần tử hiện tại
            else: # nếu loại ký tự hiện tại không phải là ký tự đặc biệt
                if current_type: # nếu có loại ký tự hiện tại
                    result.append(current_type + str(current_length)) # thêm phần tử hiện tại vào danh sách kết quả
                current_type = 'S' # cập nhật loại ký tự hiện tại thành ký tự đặc biệt
                current_length = 1  # đặt độ dài của phần tử hiện tại thành 1
    
    if current_type: # nếu có loại ký tự hiện tại
        result.append(current_type + str(current_length)) # thêm phần tử cuối cùng vào danh sách kết quả
    return result


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_path", help="path of training dataset after split", type=str, required=True) # đường dẫn đến tập dữ liệu đầu vào
    parser.add_argument("--output_path", help="path of output dataset (ready for training)", type=str, required=True) # đường dẫn đến tập dữ liệu đầu ra
    args = parser.parse_args()
    
    input_dataset = args.dataset_path # đường dẫn đến tập dữ liệu đầu vào
    output_dataset = args.output_path # đường dẫn đến tập dữ liệu đầu ra
    f_in = open(input_dataset, 'r', encoding='utf-8', errors='ignore') # mở tập dữ liệu đầu vào với chế độ đọc
    f_out = open(output_dataset, 'w', encoding='utf-8', errors='ignore') # mở tập dữ liệu đầu ra với chế độ ghi

    lines = f_in.readlines() # đọc tất cả các dòng trong tập dữ liệu đầu vào

    for line in lines: # lặp qua từng dòng trong tập dữ liệu đầu vào
        password = line[:-1] # loại bỏ ký tự xuống dòng ở cuối dòng
        prompt = ' '.join(get_pattern(password)) # gọi hàm get_pattern để lấy danh sách các chuỗi mô tả kiểu ký tự của mật khẩu
        new_line = prompt + ' <SEP> ' + ' '.join(list(password)) + '\n' # tạo dòng mới theo định dạng "pattern <SEP> password"
        f_out.write(new_line) # ghi dòng mới vào tập dữ liệu đầu ra
