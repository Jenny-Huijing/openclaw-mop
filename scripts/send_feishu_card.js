/**
 * 发送飞书卡片消息
 * 
 * 使用方法:
 * node send_feishu_card.js
 */

const FEISHU_WEBHOOK = process.env.FEISHU_WEBHOOK_URL || '';

const cardMessage = {
  "msg_type": "interactive",
  "card": {
    "config": {
      "wide_screen_mode": true
    },
    "header": {
      "template": "blue",
      "title": {
        "content": "📱 小红书内容创作完成",
        "tag": "plain_text"
      }
    },
    "elements": [
      {
        "tag": "div",
        "text": {
          "content": "**平安银行小姐姐** 的最新创作",
          "tag": "lark_md"
        }
      },
      {
        "tag": "hr"
      },
      {
        "tag": "div",
        "text": {
          "content": "📝 **内容预览**\n\n姐妹们！最近央行的新措施大家都刷到了吧～💸\n\n作为在**平安银行**搬砖3年的小客服，今天跟大家唠唠降息背景下，我自己常用的一些**钱袋子打理思路**供参考哈👇\n\n**1️⃣ 灵活存取的\"活钱罐\"**\n平时要用的零花钱，放在能随取随用的地方\n\n**2️⃣ 中期稳定的\"安心筐\"**\n半年到一年的钱，选波动小的打理方式\n\n**3️⃣ 长期规划的\"成长瓶\"**\n旅行基金、养老储备，搭配长期配置",
          "tag": "lark_md"
        }
      },
      {
        "tag": "note",
        "elements": [
          {
            "tag": "plain_text",
            "content": "⚠️ 理财有风险，投资需谨慎"
          }
        ]
      },
      {
        "tag": "hr"
      },
      {
        "tag": "div",
        "text": {
          "content": "🏷️ **标签**：#理财 #银行 #降息 #理财攻略 #银行小姐姐\n📊 **状态**：待审核 ✅\n🖼️ **配图**：2张（AI生成）",
          "tag": "lark_md"
        }
      },
      {
        "tag": "action",
        "actions": [
          {
            "tag": "button",
            "text": {
              "tag": "plain_text",
              "content": "✅ 去平台审核"
            },
            "type": "primary",
            "url": "http://localhost/"
          }
        ]
      }
    ]
  }
};

async function sendCard() {
  try {
    const response = await fetch(FEISHU_WEBHOOK, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(cardMessage)
    });
    
    const result = await response.json();
    console.log('发送结果:', result);
  } catch (error) {
    console.error('发送失败:', error);
  }
}

if (FEISHU_WEBHOOK) {
  sendCard();
} else {
  console.log('请设置 FEISHU_WEBHOOK_URL 环境变量');
  console.log('示例: export FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxx');
}
