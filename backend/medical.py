# Make sure to install the accelerate library first via `pip install accelerate`
from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image
import requests
import torch
import os
from logger import Logger


class MedicalModel:
    """
    医学诊断AI模型操作类库

    使用MedGemma模型进行医学图像诊断分析
    """

    logger = None

    def __init__(self, model_id: str = ""):
        """
        初始化医学诊断模型

        Args:
            model_id: 模型ID，默认为""
        """
        self.logger = Logger().logger
        self.model_id = model_id
        self.device_map = "cuda:0" if torch.cuda.is_available() else "cpu"
        # self.device_map = "cpu"
        self.torch_dtype = (
            torch.bfloat16 if torch.cuda.is_available() else torch.float32
        )
        self.logger.info(f"使用设备: {self.device_map}, 数据类型: {self.torch_dtype}")
        try:

            self.model = AutoModelForImageTextToText.from_pretrained(
                model_id,
                dtype=self.torch_dtype,
                device_map=self.device_map,
            )

            self.processor = AutoProcessor.from_pretrained(model_id)

        except Exception as e:
            raise RuntimeError(f"无法加载模型 {model_id}: {e}")

    def medical(
        self,
        user_name: str,
        prompt_text: str,
        image_path: str,
        max_new_tokens: int = 2048,
        do_sample: bool = False,
    ):
        """
        执行医学诊断

        Args:
            user_name: 用户名称
            prompt_text: 医学文字描述
            image_path: 影像照片路径
            max_new_tokens: 最大生成token数
            do_sample: 是否使用采样

        Returns:
            Dict包含分析结果和元信息

        Raises:
            FileNotFoundError: 图像文件不存在
            ValueError: 参数无效
            RuntimeError: 推理过程出错
        """
        # 参数验证
        if not user_name or not user_name.strip():
            raise ValueError("用户名称不能为空")

        if not prompt_text or not prompt_text.strip():
            raise ValueError("医学文字描述不能为空")

        # if not image_path or not os.path.exists(image_path):
        #    raise FileNotFoundError(f"影像照片文件不存在: {image_path}")

        try:
            if image_path:
                # 将相对路径转换为绝对路径
                image_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    image_path,
                )

            if image_path and os.path.exists(image_path):
                # 加载图像
                image = Image.open(image_path)

                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "image": image},
                            {"type": "text", "text": prompt_text},
                        ],
                    }
                ]
            else:
                messages = [
                    {"role": "user", "content": [{"type": "text", "text": prompt_text}]}
                ]

            inputs = self.processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            ).to(self.model.device, dtype=self.model.dtype)
            self.logger.info(
                f"使用设备: {self.model.device}, 数据类型: {self.model.dtype}"
            )
            '''
            inputs = self.processor.apply_chat_template(
                messages, add_generation_prompt=True, tokenize=True,
                return_dict=True, return_tensors="pt"
            )

            device = next(self.model.parameters()).device
            print("new:"+str(device))
            inputs = {
                k: (v.to(device=device, dtype=self.model.dtype) if torch.is_floating_point(v) else v.to(device=device))
                for k, v in inputs.items()
            }
            '''

            input_len = inputs["input_ids"].shape[-1]

            with torch.inference_mode():
                generation = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=do_sample,
                    pad_token_id=self.model.config.eos_token_id[0],
                )
                generation = generation[0][input_len:]

            result = self.processor.decode(generation, skip_special_tokens=True)
            return result
        except Exception as e:
            raise RuntimeError(f"诊断失败: {e}")
