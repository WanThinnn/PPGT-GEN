# Đây là file chính chứa implementation của bộ tokenizer xử lý mật khẩu

from typing import Any, Dict, List, overload
import torch
import json
import os
from transformers.tokenization_utils import PreTrainedTokenizer

char = str

class CharTokenizer(PreTrainedTokenizer):
    '''
    Class này được viết để xử lý các ký tự trong mật khẩu.
    Nó kế thừa từ lớp PreTrainedTokenizer của thư viện transformers.
    '''
    # Đọc file vocab.json để tạo bộ encoder (từ token → id) và decoder (từ id → token)
    # Thiết lập các token đặc biệt: BOS (Begin Of Sequence), EOS (End Of Sequence), SEP (Separator), UNK (Unknown), PAD (Padding)
    def __init__(
        self,
        vocab_file,
        add_bos_and_eos: bool = True,
        padding_side='right',
        bos_token=None,
        eos_token=None,
        sep_token=None,
        unk_token=None,
        pad_token=None,
    ):
        super().__init__(
            bos_token=bos_token,
            eos_token=eos_token,
            pad_token=pad_token,
            sep_token=sep_token,
            unk_token=unk_token,
        )
        self.add_bos_and_eos = add_bos_and_eos
        self.padding_side = padding_side
            
        with open(vocab_file, encoding="utf-8") as vocab_handle:
            self.encoder = json.load(vocab_handle)
        # vocab_file = os.path.join(os.path.dirname(__file__), vocab_file)
        # with open(vocab_file, encoding="utf-8") as vocab_handle:
        #     self.encoder = json.load(vocab_handle)

        
        self.decoder = {v: k for k, v in self.encoder.items()}

        self.bos_token_id = self.encoder[self.bos_token]
        self.eos_token_id = self.encoder[self.eos_token]
        self.sep_token_id = self.encoder[self.sep_token]
        self.pad_token_id = self.encoder[self.pad_token]
        self.unk_token_id = self.encoder[self.unk_token]



    @property
    def vocab_size(self):
        '''
        Hàm này trả về kích thước của vocab (số lượng token trong vocab).
        Nó sẽ trả về độ dài của bộ mã hóa (encoder) đã được tạo ra từ file vocab.json.
        '''
        return len(self.encoder)

    def get_vocab(self):
        '''
        Hàm này trả về bộ mã hóa (encoder) đã được tạo ra từ file vocab.json.
        Nó sẽ trả về một dictionary chứa các token và ID tương ứng.
        '''
        return dict(self.encoder)
    
    # Chia text thành các token (hiện tại dùng split(' '))
    def _tokenize(self, text: str) -> List[char]:
        '''
        Hàm này nhận vào một chuỗi văn bản và trả về danh sách các token.
        Nó sẽ sử dụng phương thức split(' ') để chia văn bản thành các token dựa trên khoảng trắng.
        Nếu văn bản rỗng, nó sẽ trả về một danh sách rỗng.
        Nếu không, nó sẽ trả về danh sách các token đã được chia.
        
        :param text: chuỗi văn bản cần chia thành các token
        :return: danh sách các token đã được chia
        
        '''
        if text == '':
            return []
        # result = []
        # while len(text) != 0:
        #     is_hit = False
        #     for vocab in self.encoder:
        #         if text.startswith(vocab):
        #             result.append(vocab)
        #             text = text[len(vocab):]
        #             is_hit = True
        #             break
        #     if not is_hit:
        #         result.append(self.unk_token)
        #         text = text[1:]
        return text.strip(' ').split(' ')

    # Chuyển token thành id tương ứng
    def _convert_token_to_id(self, token):
        """Converts a token (str) in an id using the vocab.
        
        :param token: token cần chuyển đổi
        :return: id tương ứng của token trong vocab        
        """
        return self.encoder.get(token, self.encoder.get(self.unk_token))

    # Chuyển id thành token tương ứng
    def _convert_id_to_token(self, index):
        """Converts an index (integer) in a token (str) using the vocab.
        
        :param index: id cần chuyển đổi
        :return: token tương ứng của id trong vocab
        
        
        """
        return self.decoder.get(index)
    
    def convert_tokens_to_string(self, tokens):
        """Converts a sequence of tokens (string) in a single string.
        
        :param tokens: danh sách các token cần chuyển đổi
        :return: chuỗi văn bản tương ứng với danh sách các token
        
        
        """
        text = "".join(tokens)
        return text
    
    # Mã hóa text thành sequence các id
    def encode(self, text: str, return_is_tensor=False) -> Any:
        '''
        Hàm này nhận vào một chuỗi văn bản và trả về danh sách các id tương ứng với các token trong văn bản.
        Nó sẽ sử dụng phương thức _tokenize để chia văn bản thành các token, sau đó chuyển đổi từng token thành id bằng phương thức _convert_token_to_id.
        
        :param text: chuỗi văn bản cần mã hóa
        :param return_is_tensor: tham số boolean để xác định có trả về tensor hay không
        :return: danh sách các id tương ứng với các token trong văn bản
        
        '''
        indices: List[int] = [self.encoder.get(c, self.unk_token_id) for c in self._tokenize(text)]
        if self.add_bos_and_eos:
            indices = [self.bos_token_id] + indices + [self.eos_token_id]
        if return_is_tensor:
            return torch.tensor(indices)
        else:
            return indices
    
    def encode_forgen(self, text: str) -> torch.Tensor:
        '''
        Hàm này nhận vào một chuỗi văn bản và trả về tensor chứa các id tương ứng với các token trong văn bản.
        Nó sẽ sử dụng phương thức _tokenize để chia văn bản thành các token, sau đó chuyển đổi từng token thành id bằng phương thức _convert_token_to_id.
        
        :param text: chuỗi văn bản cần mã hóa
        :return: tensor chứa các id tương ứng với các token trong văn bản
        
        
        '''
        indices: List[int] = [self.encoder[c] for c in self._tokenize(text)]
        indices = [self.bos_token_id] + indices
        return torch.tensor(indices)
    
    # Giải mã sequence các id thành text
    def decode(self, indices: torch.Tensor) -> str:
        '''
        Hàm này nhận vào một tensor chứa các id và trả về chuỗi văn bản tương ứng với các id đó.
        Nó sẽ chuyển đổi từng id thành token bằng phương thức _convert_id_to_token, sau đó nối các token lại thành một chuỗi văn bản.
        
        :param indices: tensor chứa các id cần giải mã
        :return: chuỗi văn bản tương ứng với các id trong tensor
        
        
        '''
        chars = []
        for index in indices:
            index = int(index)
            if index in [self.bos_token_id, self.eos_token_id, self.pad_token_id]:
                continue
            elif index == self.sep_token_id:
                decode_ans = ' '
            else:
                decode_ans = self.decoder[index]
            chars.append(decode_ans)
        return "".join(chars)


    # Giao diện chính để tokenize text (hỗ trợ padding và không padding)
    @overload
    def __call__(self, texts: str, max_len=None, padding=False) -> Dict: # Hàm này nhận vào một chuỗi văn bản và trả về một dictionary chứa các id và attention masks tương ứng với các token trong văn bản.
        ...
    @overload
    def __call__(self, texts: list, max_len=None, padding=False) -> Dict: # Hàm này nhận vào một danh sách các chuỗi văn bản và trả về một dictionary chứa các id và attention masks tương ứng với các token trong từng văn bản.
        ...
    def __call__(self, texts, max_len=None, padding=False) -> Dict:
        '''
        Hàm này nhận vào một chuỗi văn bản hoặc một danh sách các chuỗi văn bản và trả về một dictionary chứa các id và attention masks tương ứng với các token trong từng văn bản.
        Nếu padding là True, nó sẽ thêm các token đệm (padding tokens) vào cuối chuỗi để đảm bảo tất cả các chuỗi có cùng độ dài max_len.
        Nếu padding là False, nó sẽ không thêm token đệm và trả về độ dài thực tế của từng chuỗi.
        
        :param texts: chuỗi văn bản hoặc danh sách các chuỗi văn bản cần mã hóa
        :param max_len: độ dài tối đa của chuỗi (nếu padding là True)
        :param padding: tham số boolean để xác định có thêm token đệm hay không
        :return: dictionary chứa các id và attention masks tương ứng với các token trong từng văn bản
        
        '''
        if not padding: # Nếu không cần padding, chỉ cần mã hóa văn bản và trả về các id và attention masks tương ứng
            if type(texts) == str: # Nếu texts là một chuỗi văn bản
                input_ids = self.encode(texts) # Mã hóa văn bản thành các id
                attention_masks = [1] * len(input_ids) # Tạo attention masks với tất cả các giá trị là 1 (tức là tất cả các token đều được chú ý)
                result = {"input_ids":input_ids, "attention_masks":attention_masks} # Tạo dictionary chứa các id và attention masks
                return result # Trả về dictionary chứa các id và attention masks
            else: # Nếu texts là một danh sách các chuỗi văn bản
                assert(type(texts)==list) # Kiểm tra xem texts có phải là danh sách hay không
                result = {"input_ids":[], "attention_masks":[]} # Tạo dictionary chứa các id và attention masks
                for text in texts: # Lặp qua từng chuỗi văn bản trong danh sách
                    input_ids = self.encode(text) # Mã hóa văn bản thành các id
                    attention_masks = [1] * len(input_ids) # Tạo attention masks với tất cả các giá trị là 1 (tức là tất cả các token đều được chú ý)
                    result["input_ids"].append(input_ids) # Thêm các id vào danh sách trong dictionary
                    result["attention_masks"].append(attention_masks) # Thêm attention masks vào danh sách trong dictionary
                return result # Trả về dictionary chứa các id và attention masks
        else: # Nếu cần padding, thêm token đệm vào cuối chuỗi để đảm bảo tất cả các chuỗi có cùng độ dài max_len
            assert(max_len) # Kiểm tra xem max_len có được cung cấp hay không
            if self.padding_side == 'right': # Nếu padding ở bên phải chuỗi
                if type(texts) == str: # Nếu texts là một chuỗi văn bản
                    input_ids = self.encode(texts) # Mã hóa văn bản thành các id
                    length = len(input_ids) # Lấy độ dài của chuỗi đã mã hóa
                    input_ids += [self.pad_token_id] * (max_len - length) # Thêm token đệm vào cuối chuỗi để đảm bảo độ dài bằng max_len
                    attention_masks = [1] * length + [0] * (max_len - length) # Tạo attention masks với các giá trị là 1 cho các token đã mã hóa và 0 cho các token đệm
                    result = {"input_ids":input_ids, "attention_masks":attention_masks} # Tạo dictionary chứa các id và attention masks
                    return result # Trả về dictionary chứa các id và attention masks
                else: # Nếu texts là một danh sách các chuỗi văn bản
                    assert(type(texts)==list) # Kiểm tra xem texts có phải là danh sách hay không
                    result = {"input_ids":[], "attention_masks":[]} # Tạo dictionary chứa các id và attention masks
                    for text in texts: # Lặp qua từng chuỗi văn bản trong danh sách
                        input_ids = self.encode(text) # Mã hóa văn bản thành các id
                        length = len(input_ids) # Lấy độ dài của chuỗi đã mã hóa
                        input_ids += [self.pad_token_id] * (max_len - length) # Thêm token đệm vào cuối chuỗi để đảm bảo độ dài bằng max_len
                        attention_masks = [1] * length + [0] * (max_len - length) # Tạo attention masks với các giá trị là 1 cho các token đã mã hóa và 0 cho các token đệm
                        result["input_ids"].append(input_ids) # Thêm các id vào danh sách trong dictionary
                        result["attention_masks"].append(attention_masks) # Thêm attention masks vào danh sách trong dictionary
                    return result # Trả về dictionary chứa các id và attention masks
            else:   # Nếu padding ở bên trái chuỗi
                assert(self.padding_side=="left") # Kiểm tra xem padding_side có phải là 'left' hay không
                if type(texts) == str: # Nếu texts là một chuỗi văn bản
                    input_ids = self.encode(texts) # Mã hóa văn bản thành các id
                    length = len(input_ids) # Lấy độ dài của chuỗi đã mã hóa
                    padding = [self.pad_token_id] * (max_len - length) # Thêm token đệm vào đầu chuỗi để đảm bảo độ dài bằng max_len
                    input_ids = padding + input_ids # Thêm token đệm vào đầu chuỗi
                    attention_masks = [0] * (max_len - length) + [1] * length # Tạo attention masks với các giá trị là 0 cho các token đệm và 1 cho các token đã mã hóa
                    result = {"input_ids":input_ids, "attention_masks":attention_masks} # Tạo dictionary chứa các id và attention masks
                    return result # Trả về dictionary chứa các id và attention masks
                else: # Nếu texts là một danh sách các chuỗi văn bản
                    assert(type(texts)==list) # Kiểm tra xem texts có phải là danh sách hay không
                    result = {"input_ids":[], "attention_masks":[]} # Tạo dictionary chứa các id và attention masks
                    for text in texts: # Lặp qua từng chuỗi văn bản trong danh sách
                        input_ids = self.encode(text)   # Mã hóa văn bản thành các id
                        length = len(input_ids) # Lấy độ dài của chuỗi đã mã hóa
                        padding = [self.pad_token_id] * (max_len - length) # Thêm token đệm vào đầu chuỗi để đảm bảo độ dài bằng max_len
                        input_ids = padding + input_ids # Thêm token đệm vào đầu chuỗi
                        attention_masks = [0] * (max_len - length) + [1] * length # Tạo attention masks với các giá trị là 0 cho các token đệm và 1 cho các token đã mã hóa
                        result["input_ids"].append(input_ids) # Thêm các id vào danh sách trong dictionary
                        result["attention_masks"].append(attention_masks) # Thêm attention masks vào danh sách trong dictionary
                    return result

    def batch_decode(self, indices:torch.Tensor) -> List[str]:
        '''
        Hàm này nhận vào một tensor chứa các id và trả về danh sách các chuỗi văn bản tương ứng với các id đó.
        Nó sẽ chuyển đổi từng id thành token bằng phương thức _convert_id_to_token, sau đó nối các token lại thành một chuỗi văn bản.
        
        :param indices: tensor chứa các id cần giải mã
        :return: danh sách các chuỗi văn bản tương ứng với các id trong tensor
    
        
        '''
        result = [] # Tạo danh sách rỗng để lưu trữ các chuỗi văn bản đã giải mã
        for i in range(indices.shape[0]): # Lặp qua từng tensor trong batch
            result.append(self.decode(indices[i])) # Giải mã từng tensor thành chuỗi văn bản
        return result # Trả về danh sách các chuỗi văn bản đã giải mã


def main():
    vocab_file = "vocab.json" # Đường dẫn đến file vocab.json chứa các token và ID tương ứng

    tokenizer = CharTokenizer(vocab_file=vocab_file,  # Tạo tokenizer từ file vocab.json
                              bos_token="<BOS>", # Token bắt đầu chuỗi
                              eos_token="<EOS>",# Token kết thúc chuỗi
                              sep_token="<SEP>", # Token phân cách
                              unk_token="<UNK>", # Token cho ký tự không xác định
                              pad_token="<PAD>" # Token đệm
                            )

    print(f"vocab_size: {tokenizer.vocab_size}") # In kích thước vocab

    texts = ["L4 N3 S1 <SEP> P a s s 1 2 3 $"] # Danh sách các chuỗi văn bản cần mã hóa và giải mã

    for text in texts:  # Lặp qua từng chuỗi văn bản trong danh sách
        indices = tokenizer.encode(text, return_is_tensor=True) # Mã hóa văn bản thành các id
        reconstructed_text = tokenizer.decode(indices) # Giải mã các id thành chuỗi văn bản
        
        print('inputs:{}'.format(text)) # In chuỗi văn bản đầu vào
        print('encoded:{}'.format(indices)) # In các id tương ứng với chuỗi văn bản
        print('decoded:{}'.format(reconstructed_text)) # In chuỗi văn bản đã giải mã


if __name__ == "__main__":
    main()
