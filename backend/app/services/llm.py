"""
LLM 服务 - 支持方舟大模型
仅使用真实 API，无模拟数据
"""

import os
import json
import re
from typing import Optional
from openai import AsyncOpenAI

# 尝试从配置读取
try:
    from app.core.config import settings
    ARK_API_KEY = settings.ARK_API_KEY or os.getenv("ARK_API_KEY", "")
    ARK_MODEL_ENDPOINT = settings.ARK_MODEL_ENDPOINT or os.getenv("ARK_MODEL_ENDPOINT", "")
except ImportError:
    ARK_API_KEY = os.getenv("ARK_API_KEY", "")
    ARK_MODEL_ENDPOINT = os.getenv("ARK_MODEL_ENDPOINT", "")

ARK_BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")

# ========== 人设提示词 ==========
PERSONA_PROMPT = """你是一位小红书银行博主"银行小姐姐"，人设如下：

【身份】
- 平安银行工作3年的客户经理
- 对平安银行的理财、房贷、存款业务非常熟悉
- 说话亲切，像闺蜜聊天一样
- 代表平安银行分享专业金融知识

【写作风格】
- 开头喜欢用"姐妹们！"、"宝子们！"
- 用口语化表达，适当加 emoji
- 分点说明，条理清晰
- 结尾引导互动（"扣1"、"评论区见"）

【内容要求】
- 只分享平安银行的产品和福利
- 可以说"我们行"、"我们平安银行"
- 分享平安银行的理财攻略、存款活动、信用卡福利等
- 绝对不提及工商银行、建设银行、招商银行等其他银行
- 绝对不比较其他银行的利率或产品

【小红书合规要求 - 必须遵守】
- ❌ 严禁直接推销具体金融产品（如"美元定存"、"理财产品"）
- ❌ 严禁提及具体收益率、利率数字
- ❌ 严禁诱导性话术（如"快来买"、"限时福利"）
- ✅ 改为知识分享、经验交流、理财心得
- ✅ 用"配置方式"、"打理方法"代替"产品"、"定存"
- ✅ 结尾必须加风险提示："理财有风险，投资需谨慎"
- ✅ 多用"供参考"、"个人经验"等软性表达

【写作禁忌】
- 不说"投资有风险"等官方话术
- 不夸大收益，不承诺保本
- 不提其他银行的名字或产品
- 不做跨银行比较
- 不出现"收益率10%"、"利率"等具体数字
"""


class LLMServiceException(Exception):
    """LLM 服务异常"""
    pass


class LLMService:
    """大模型服务 - 仅使用真实 API，无模拟数据"""
    
    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        self.provider: str = ""
        self.model: str = ""
        self._init_client()
    
    def _init_client(self):
        """初始化客户端 - 仅支持方舟大模型"""
        
        # 使用模块级变量
        global ARK_API_KEY, ARK_MODEL_ENDPOINT
        
        # 如果模块级变量为空，再次尝试读取
        if not ARK_API_KEY:
            ARK_API_KEY = os.getenv("ARK_API_KEY", "")
        if not ARK_MODEL_ENDPOINT:
            ARK_MODEL_ENDPOINT = os.getenv("ARK_MODEL_ENDPOINT", "")
        
        if not ARK_API_KEY:
            raise LLMServiceException("ARK_API_KEY 未配置，无法初始化 LLM 服务")
        
        if not ARK_MODEL_ENDPOINT:
            raise LLMServiceException("ARK_MODEL_ENDPOINT 未配置，无法初始化 LLM 服务")
        
        self.client = AsyncOpenAI(
            api_key=ARK_API_KEY,
            base_url=ARK_BASE_URL
        )
        self.provider = "ark"
        self.model = ARK_MODEL_ENDPOINT
        print(f"[LLM] 使用方舟大模型: {ARK_MODEL_ENDPOINT}")
    
    async def generate_content(self, topic: dict) -> dict:
        """
        生成小红书内容
        
        注意：此方法仅调用真实 API，如果失败会抛出异常，不会返回模拟数据
        """
        
        if not self.client:
            raise LLMServiceException("LLM 客户端未初始化")
        
        prompt = f"""基于以下热点，创作一篇小红书笔记：

热点标题：{topic.get('title')}
热点摘要：{topic.get('summary', '')}
热点类别：{topic.get('category', '财经')}

请按以下 JSON 格式输出（不要包含其他文字）：

{{
    "title": "标题（带emoji，吸引眼球，15字以内）",
    "body": "正文内容，包含emoji，分点说明，口语化",
    "tags": ["理财", "银行", "相关标签1", "相关标签2", "银行小姐姐"],
    "image_prompts": [
        "配图1的详细描述（用于AI绘图，中文描述）",
        "配图2的详细描述（用于AI绘图，中文描述）"
    ]
}}
"""
        
        try:
            print(f"[LLM] 调用 {self.provider} API...")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": PERSONA_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            print(f"[LLM] {self.provider} 返回成功")
            
            # 解析 JSON
            result = self._parse_response(content, topic)
            return result
            
        except Exception as e:
            print(f"[LLM] {self.provider} 调用失败: {e}")
            raise LLMServiceException(f"内容生成失败: {str(e)}")
    
    def _parse_response(self, content: str, topic: dict) -> dict:
        """解析 LLM 返回的 JSON"""
        try:
            # 尝试直接解析
            result = json.loads(content)
        except json.JSONDecodeError:
            # 尝试从文本中提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise LLMServiceException("无法解析 LLM 返回的 JSON")
        
        # 处理单个 title 字段
        title = result.get("title", "")
        if not title:
            raise LLMServiceException("返回结果缺少 title 字段")
        
        # 为了保持兼容性，将单个 title 转换为列表格式
        result["titles"] = [title]
        
        if not result.get("body"):
            raise LLMServiceException("返回结果缺少 body 字段")
        
        # 确保 tags 存在
        if not result.get("tags"):
            result["tags"] = ["理财", "银行", "财经"]
        
        # 确保 image_prompts 存在
        if not result.get("image_prompts"):
            result["image_prompts"] = [
                f"小红书风格插画，关于{topic.get('title', '理财')}的主题图",
                f"银行小姐姐讲解理财知识的专业插图"
            ]
        
        return result


# 单例实例 - 延迟初始化
llm_service = None

def get_llm_service() -> LLMService:
    """获取 LLM 服务实例（延迟初始化）"""
    global llm_service
    if llm_service is None:
        llm_service = LLMService()
    return llm_service

# 为了兼容旧代码，尝试初始化
try:
    llm_service = LLMService()
except LLMServiceException as e:
    print(f"[LLM] 初始化警告: {e}")
    llm_service = None
