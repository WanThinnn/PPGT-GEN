'''
File này được viết để sinh mật khẩu bằng cách sử dụng mô hình GPT-2 đã được huấn luyện trước đó.
Nó sẽ sử dụng thư viện transformers để tải mô hình GPT-2 và thư viện PyTorch để xử lý tensor và GPU.
Nó sẽ sử dụng thư viện argparse để xử lý các tham số dòng lệnh và thư viện os để làm việc với hệ thống tệp.
Nó sẽ sử dụng thư viện threading để xử lý đa luồng và thư viện time để đo thời gian thực thi.
Nó sẽ sử dụng một lớp kế thừa từ threading.Thread để hỗ trợ trả về giá trị từ luồng.


'''

from transformers import (
    GPT2LMHeadModel  # Nhập mô hình GPT-2 để tạo văn bản (ở đây dùng để sinh mật khẩu)
)
import time  # Thư viện để đo thời gian thực thi
import threading  # Thư viện để xử lý đa luồng
import torch  # Thư viện PyTorch cho tính toán tensor và sử dụng GPU
from tokenizer import CharTokenizer  # Nhập tokenizer tùy chỉnh từ file tokenizer
import argparse  # Thư viện để xử lý tham số dòng lệnh
import os  # Thư viện để làm việc với hệ thống tệp

MAX_LEN = 32  # Độ dài tối đa của chuỗi đầu ra (mật khẩu), phải khớp với kích thước đầu vào của mô hình

class ThreadBase(threading.Thread):
    """Lớp kế thừa threading.Thread để hỗ trợ trả về giá trị từ luồng"""
    def __init__(self, target=None, args=()):
        '''
        Hàm khởi tạo lớp ThreadBase
        
        :param target: Hàm mục tiêu sẽ chạy trong luồng
        :param args: Các tham số truyền vào hàm mục tiêu
        
        '''
        super().__init__()  # Gọi hàm khởi tạo của lớp cha threading.Thread
        self.func = target  # Hàm mục tiêu sẽ chạy trong luồng
        self.args = args  # Các tham số truyền vào hàm mục tiêu
 
    def run(self):
        '''
        Hàm chạy trong luồng
        
        :return: Không trả về giá trị
        '''
        self.result = self.func(*self.args)  # Chạy hàm mục tiêu và lưu kết quả vào self.result
 
    def get_result(self):
        '''
        Hàm để lấy kết quả từ luồng
        
        :return: Kết quả của luồng hoặc None nếu có lỗi xảy ra
        '''
        try:
            return self.result  # Trả về kết quả của luồng
        except Exception as e:
            print(e)  # In lỗi nếu có
            return None  # Trả về None nếu xảy ra lỗi

def gen_sample(test_model_path, tokenizer, GEN_BATCH_SIZE, GPU_ID):
    """Hàm tạo mẫu mật khẩu bằng mô hình GPT-2 trên một GPU cụ thể
    
    :param test_model_path: Đường dẫn đến mô hình đã huấn luyện
    :param tokenizer: Tokenizer để mã hóa đầu vào
    :param GEN_BATCH_SIZE: Kích thước batch cho việc sinh mẫu
    :param GPU_ID: ID của GPU được sử dụng (0, 1, ...)
    :return: Danh sách các mật khẩu sinh ra
    
    """
    model = GPT2LMHeadModel.from_pretrained(test_model_path)  # Tải mô hình GPT-2 từ đường dẫn đã huấn luyện
    
    # device = "cuda:" + str(GPU_ID)  # Xác định thiết bị GPU (ví dụ: cuda:0, cuda:1, ...)
    device = torch.device("cuda:0") # Chọn GPU đầu tiên (cuda:0) để chạy mô hình (trường hợp chỉ có một GPU)
    model.to(device)  # Chuyển mô hình lên GPU được chỉ định

    inputs = ""  # Đầu vào rỗng để mô hình tự sinh từ đầu
    tokenizer_forgen_result = tokenizer.encode_forgen(inputs)  # Mã hóa đầu vào bằng tokenizer
    passwords = set()  # Tập hợp để lưu các mật khẩu sinh ra (loại bỏ trùng lặp)
    
    outputs = model.generate(
        input_ids=tokenizer_forgen_result.view([1, -1]).to(device),  # Chuyển input_ids thành tensor 2D và đưa lên GPU
        pad_token_id=tokenizer.pad_token_id,  # ID của token đệm
        max_length=MAX_LEN,  # Độ dài tối đa của chuỗi sinh ra
        do_sample=True,  # Sử dụng lấy mẫu ngẫu nhiên thay vì chọn token có xác suất cao nhất
        num_return_sequences=GEN_BATCH_SIZE,  # Số lượng chuỗi cần sinh trong một lần
    )
    outputs = tokenizer.batch_decode(outputs)  # Giải mã các chuỗi tensor thành văn bản
    for output in outputs:
        passwords.add(output)  # Thêm từng mật khẩu vào tập hợp

    return [*passwords,]  # Trả về danh sách các mật khẩu từ tập hợp

def gen_parallel(vocab_file, batch_size, test_model_path, N, gen_passwords_path, num_gpus, gpu_index):
    """Hàm sinh mật khẩu song song trên nhiều GPU
    
    :param vocab_file: Đường dẫn đến file vocab chứa các token và ID tương ứng
    :param batch_size: Kích thước batch cho việc sinh mẫu
    :param test_model_path: Đường dẫn đến mô hình đã huấn luyện
    :param N: Tổng số mật khẩu cần sinh
    :param gen_passwords_path: Đường dẫn lưu file đầu ra chứa mật khẩu sinh ra
    :param num_gpus: Số lượng GPU có sẵn
    :param gpu_index: Chỉ số GPU bắt đầu (thường là 0 hoặc 1)
    :return: Không trả về giá trị, nhưng sẽ ghi mật khẩu sinh ra vào file đầu ra
    
    """
    print(f'Load tokenizer.')
    tokenizer = CharTokenizer(vocab_file=vocab_file,  # Tải tokenizer từ file vocab
                              bos_token="<BOS>",  # Token bắt đầu chuỗi
                              eos_token="<EOS>",  # Token kết thúc chuỗi
                              sep_token="<SEP>",  # Token phân cách
                              unk_token="<UNK>",  # Token cho ký tự không xác định
                              pad_token="<PAD>"  # Token đệm
                              )
    tokenizer.padding_side = "left"  # Đặt đệm ở bên trái chuỗi

    # Kiểm tra và thực hiện sinh song song trên GPU
    if not torch.cuda.is_available():
        print('ERROR! GPU not found!')  # Báo lỗi nếu không có GPU
    else:
        total_start = time.time()  # Bắt đầu đo thời gian toàn bộ quá trình
        threads = {}  # Dictionary để lưu các luồng và chỉ số của chúng
        total_passwords = []  # Danh sách lưu tất cả mật khẩu sinh ra

        total_round = N // batch_size  # Tính số vòng lặp cần thiết dựa trên tổng số mật khẩu và kích thước batch
        print('*' * 30)
        print(f'Generation begin.')
        print('Total generation needs {} batchs.'.format(total_round))

        i = 0  # Biến đếm số batch đã xử lý
        while (i < total_round or len(threads) > 0):  # Tiếp tục khi chưa đủ batch hoặc còn luồng đang chạy
            if len(threads) == 0:  # Nếu không có luồng nào đang chạy
                for gpu_id in range(num_gpus):  # Duyệt qua các GPU có sẵn
                    if i < total_round:  # Nếu vẫn còn batch cần xử lý
                        t = ThreadBase(target=gen_sample, args=(test_model_path, tokenizer, batch_size, gpu_id + gpu_index))
                        t.start()  # Bắt đầu luồng
                        threads[t] = i  # Lưu luồng và chỉ số batch tương ứng
                        i += 1  # Tăng biến đếm
            
            # Kiểm tra các luồng đã hoàn thành
            temp_threads = threads.copy()  # Sao chép dictionary để tránh lỗi khi thay đổi trong vòng lặp
            for t in temp_threads:
                t.join()  # Chờ luồng hoàn thành
                if not t.is_alive():  # Nếu luồng đã kết thúc
                    new_passwords = t.get_result()  # Lấy kết quả từ luồng
                    new_num = len(new_passwords)  # Đếm số mật khẩu mới sinh ra
                    total_passwords += new_passwords  # Thêm vào danh sách tổng
                    print('[{}/{}] generated {}.'.format(temp_threads[t] + 1, total_round, new_num))  # In tiến độ
                    threads.pop(t)  # Xóa luồng đã hoàn thành khỏi dictionary
               
        total_passwords = set(total_passwords)  # Chuyển danh sách thành tập hợp để loại bỏ trùng lặp

        gen_passwords_path = gen_passwords_path + 'PagPassGPT_Normal-GEN' + '.txt'  # Tạo tên file đầu ra
        
        f_gen = open(gen_passwords_path, 'w', encoding='utf-8', errors='ignore')  # Mở file để ghi kết quả
        for password in total_passwords:
            f_gen.write(password + '\n')  # Ghi từng mật khẩu vào file, mỗi dòng một mật khẩu

        total_end = time.time()  # Kết thúc đo thời gian
        total_time = total_end - total_start  # Tính tổng thời gian thực thi
        
        print('Generation file saved in: {}'.format(gen_passwords_path))  # In đường dẫn file kết quả
        print('Generation done.')
        print('*' * 30)
        print('Use time:{}'.format(total_time))  # In thời gian thực thi
from pathlib import Path

if __name__ == '__main__':
    """Điểm bắt đầu của chương trình"""
    parser = argparse.ArgumentParser()
    default_vocab = str(Path(__file__).resolve().parent / "tokenizer" / "vocab.json")
    print(f"Default vocab file: {default_vocab}")
    parser.add_argument("--model_path", help="directory of pagpassgpt", type=str, required=True)  # Đường dẫn đến mô hình đã huấn luyện
    parser.add_argument("--vocabfile_path", help="path of vocab file", type=str, default=default_vocab)  # Đường dẫn file vocab
    parser.add_argument("--output_path", help="path of output file path", type=str, required=True)  # Đường dẫn thư mục đầu ra
    parser.add_argument("--generate_num", help="total guessing number", default=1000000, type=int)  # Tổng số mật khẩu cần sinh
    parser.add_argument("--batch_size", help="generate batch size", default=5000, type=int)  # Kích thước batch mỗi lần sinh
    parser.add_argument("--gpu_num", help="gpu num", default=1, type=int)  # Số lượng GPU sử dụng
    parser.add_argument("--gpu_index", help="Starting GPU index", default=0, type=int)  # Chỉ số GPU bắt đầu
    args = parser.parse_args()  # Phân tích các tham số dòng lệnh

    model_path = args.model_path  # Gán đường dẫn mô hình
    vocab_file = args.vocabfile_path  # Gán đường dẫn file vocab
    output_path = args.output_path  # Gán đường dẫn đầu ra

    n = args.generate_num  # Tổng số mật khẩu cần sinh
    batch_size = args.batch_size  # Kích thước batch
    num_gpus = args.gpu_num  # Số lượng GPU
    gpu_index = args.gpu_index  # Chỉ số GPU bắt đầu

    # create new folder to store generation passwords
    base = args.output_path.rstrip("/\\")
    output_path = os.path.join(base, str(args.generate_num)) + '/' # đường dẫn đến thư mục đầu ra để lưu trữ mật khẩu đã sinh
    folder = os.path.exists(output_path) # kiểm tra xem thư mục đã tồn tại chưa
    if not folder:
        os.makedirs(output_path)
    
    gen_parallel(vocab_file, batch_size, model_path, n, output_path, num_gpus, gpu_index)  # Gọi hàm sinh song song
