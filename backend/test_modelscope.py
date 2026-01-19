#!/usr/bin/env python3
"""
ModelScope API 测试脚本
用于验证图片生成功能
"""
import asyncio
import os
import sys

# 添加 backend 目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.modelscope_client import ModelScopeClient
from app.core.config import settings


async def test_image_generation():
    """测试图片生成"""
    print("=" * 60)
    print("ModelScope API 图片生成测试")
    print("=" * 60)

    api_key = settings.MODELSCOPE_API_KEY
    if not api_key:
        print("❌ 错误: 未设置 MODELSCOPE_API_KEY 环境变量")
        print("请在 .env 文件中设置: MODELSCOPE_API_KEY=your-token")
        return False

    print(f"✅ API Key 已配置: {api_key[:10]}...")

    async with ModelScopeClient(api_key=api_key) as client:
        # 测试 1: 简单的图片生成
        print("\n📝 测试 1: 简单的图片生成...")
        try:
            result = await client.generate(
                prompt="A golden cat sitting on a velvet cushion",
                num_images=1,
                width=512,
                height=512,
            )

            if result["success"]:
                print(f"✅ 生成成功!")
                print(f"   任务ID: {result.get('task_id')}")
                print(f"   图像数量: {len(result['images'])}")
                print(f"   处理时间: {result['processing_time']:.2f}秒")
                print(f"   质量评分: {result['quality_score']}")

                # 保存测试图片
                if result["images"]:
                    img_data = result["images"][0]["data"]
                    import base64
                    from PIL import Image
                    import io

                    img_bytes = base64.b64decode(img_data.split(",")[1])
                    img = Image.open(io.BytesIO(img_bytes))
                    img.save("test_result.jpg")
                    print(f"   图片已保存: test_result.jpg")
            else:
                print(f"❌ 生成失败: {result.get('error')}")
                return False

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False

        # 测试 2: 带风格的生成
        print("\n🎨 测试 2: 带风格的图片生成...")
        try:
            result2 = await client.generate(
                prompt="A product on white background",
                style_id="amazon_standard",
                num_images=1,
                width=1024,
                height=1024,
            )

            if result2["success"]:
                print(f"✅ 风格生成成功!")
                print(f"   使用提示词: {result2['prompt_used'][:80]}...")
            else:
                print(f"⚠️ 风格生成失败: {result2.get('error')}")

        except Exception as e:
            print(f"⚠️ 风格测试跳过: {e}")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    return True


async def main():
    """主函数"""
    success = await test_image_generation()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
