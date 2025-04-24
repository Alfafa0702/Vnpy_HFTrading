import numpy as np
import os
import lightgbm as lgb

print("当前工作目录:", os.getcwd())

# 1. 检查模型文件是否存在
if os.path.exists('lgbm_model.txt'):
    print("模型文件存在")
    print("文件大小:", os.path.getsize('lgbm_model.txt'), "字节")
else:
    print("错误：模型文件不存在！")
    exit(1)

# 2. 尝试加载模型
try:
    print("\n正在加载模型...")
    model = lgb.Booster(model_file='lgbm_model.txt')
    
    print("模型加载成功")
    print("模型类型:", type(model))
    print("模型属性:", dir(model))
    
    # 3. 创建测试数据
    test_features = np.random.random((1, 23)).astype(np.float32)
    print("\n测试数据形状:", test_features.shape)
    print("测试数据类型:", test_features.dtype)
    print("测试数据:", test_features)
    
    # 4. 尝试预测
    print("\n尝试预测...")
    prediction = model.predict(test_features)
    print("预测成功！")
    print("预测结果:", prediction)
    print("预测结果类型:", type(prediction))
    print("预测结果形状:", prediction.shape if hasattr(prediction, 'shape') else len(prediction))
    
    # 5. 测试多条数据预测
    print("\n测试多条数据预测...")
    test_features_multi = np.random.random((5, 23)).astype(np.float32)
    predictions_multi = model.predict(test_features_multi)
    print("多条预测成功！")
    print("预测结果:", predictions_multi)
    print("预测结果形状:", predictions_multi.shape if hasattr(predictions_multi, 'shape') else len(predictions_multi))
    
except Exception as e:
    print("\n错误发生:")
    print("错误类型:", type(e))
    print("错误信息:", str(e))
    import traceback
    print("\n详细错误信息:")
    traceback.print_exc() 