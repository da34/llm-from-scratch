import torch
import torch.nn as nn

# 词表大小，假设我们的词表一共有30个 token
vocab_size = 30


# 向量维度：每个 token 用一个 8 维向量来表示
# 这个数字是自己设定的参数， 实际大模型里通常是几百到几千维
embedding_dim = 8

# 创建 Embedding层，本质上就是初始化一张 30行 * 8 列的随机数表
embedding_layer = nn.Embedding(vocab_size, embedding_dim)


# 猫吃鱼的 token id
token_ids = torch.tensor([3, 15, 4])

# 查表操作：输入 token id , 返回对应的向量
vectors = embedding_layer(token_ids)

# 输出
print(vectors)
print(vectors.shape)
