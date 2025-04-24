import pandas as pd
import numpy as np

# 读取原始数据
df = pd.read_csv('all_test_features/all_test_features.csv')

# 打印原始列名
print("原始列名：")
print(df.columns.tolist())

df.rename(columns={'idx': 'datetime'}, inplace=True)

# 1. 分离特征数据和价格数据
feature_df = df.iloc[:, :24]  # 前24列（包括datetime）
price_df = df.iloc[:, 24:]    # 24列之后的所有列

print("\n特征数据列名：")
print(feature_df.columns.tolist())
print("\n价格数据列名：")
print(price_df.columns.tolist())

# 2. 分别处理空值
print(f"\n处理前的行数：{len(df)}")
feature_df = feature_df.dropna().reset_index(drop=True)
price_df = price_df.dropna().reset_index(drop=True)
print(f"处理feature空值后的行数：{len(feature_df)}")
print(f"处理price空值后的行数：{len(price_df)}")

# 3. 合并数据
final_df = pd.concat([feature_df, price_df],axis=1)
print(f"合并后的行数：{len(final_df)}")

# 4. 添加symbol和exchange列
final_df.insert(1, 'symbol', 'BTCUSDT')
final_df.insert(2, 'exchange', 'BINANCE')

# 检查是否还有空值
print("\n各列的空值数量：")
print(final_df.isnull().sum())

# 保存修复后的数据
final_df.to_csv('all_test_features/all_test_features_fixed.csv', index=False)

# 打印修复后的数据预览
print('\n修复后的数据预览：')
print(final_df.head())
print('\n修复后的列名：')
print(final_df.columns.tolist()) 