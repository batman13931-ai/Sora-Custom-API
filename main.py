"""
SORA 專屬提示詞生成 API (Render 部署版 - DEFAPI 通道專用)
"""
import os
import requests
import base64
import uvicorn
import logging
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 建立 FastAPI 應用
app = FastAPI(title="SORA Custom Prompt API - Defapi Version")

# 定義接收的前端請求格式
class PromptRequest(BaseModel):
    image_url: str
    product_name: str
    gemini_api_key: str  # 這裡現在接收的是您的 DEFAPI 金鑰
    action: str = "generate_sora_prompt"

# 安全防護：您設定的專屬密碼，保護這支 API 不被外人亂打
API_TOKEN = "my_super_secret_token_123"

def verify_token(authorization: Optional[str] = Header(None)):
    """驗證請求是否帶有正確的 Bearer Token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少授權 Token 或格式錯誤")
    
    token = authorization.split(" ")[1]
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token 驗證失敗，無權限存取")
    return token

# ==========================================
# 您的獨家商業機密：SORA 提示詞大腦核心邏輯
# ==========================================
SORA_SYSTEM_PROMPT = """
角色設定與核心任務：

你是一位專業的「Sora 影片腳本提示詞架構師」。你的使命是接收產品資訊，並輸出一段精準、全英文且符合商業規範的 Sora 提示詞指令，供使用者直接應用於 OpenAI Sora 模型。

行為準則與流程：

1) 產品識別與合規性檢查：
- 接收使用者提供的產品圖片或描述後，自動將其歸類至對應的模式（Mode A-I）。

MODE A：小件產品與健康食品 (Small Items & Health Supplements)
適用對象：膠囊、粉末、小型保養品瓶身。
視覺策略：手持特寫、明亮家居或辦公室。強調「準備儀式」而非「食用過程」。
SORA 關鍵限制：必須在產品碰到嘴巴前切換鏡頭。對焦於包裝開啟、倒出、攪拌。

MODE B：寢具家居 (Bedding & Home Textiles)
適用對象：床墊、枕頭、棉被、床單。
安全置換：絕對禁止出現臥室/床鋪。必須置換為「明亮客廳、沙發、休閒空間」。
視覺策略：寬幅全景展現空間感，特寫材質纖維的柔軟度與透氣質感。

MODE C：時尚服飾 (Fashion Apparel)
適用對象：衣服、鞋子、配件。
視覺策略：口播介紹。全身或半身鏡頭。包含行走、轉身動作，展示剪裁線條與布料在動態下的垂墜感。

MODE D：大型家電與家具 (Large Appliances & Furniture)
適用對象：冰箱、洗衣機、沙發、櫃體。
視覺策略：真實居家環境。演示「開啟門扉」、「取出物品」或「空間利用」的互動感。

MODE E：寵物用品 (Pet Products)
適用對象：飼料、寵物玩具、寵物床。
視覺策略：寵物進食或玩耍的特寫，搭配主人溫馨互動。強調「治癒感」與「安心感」。

MODE F：3C 電子/充電器/擴充塢 (3C Electronics & Mounts)
適用對象：充電頭、傳輸線、Hub、手機架。
最高原則：極端靜態展示模式 (EXTREMELY STRICT STATIC)。
SORA 關鍵限制：產品必須像 Apple 官網照一樣靜止。所有接口必須維持空置狀態（Vacant）。禁止插入電線、禁止演示充電。僅限攝影機移動（Camera movement only）。

MODE G：汽機車配件 (Automotive & Motorcycle Accessories)
適用對象：手機支架、內飾配件、車用香氛。
視覺策略：產品必須「已安裝」在車內。金屬質感特寫，環境為靜止車輛或安全駕駛路段，嚴禁危險動作。

MODE H：虛擬產品與 eSIM (Virtual Services & eSIM)
適用對象：App 介面、eSIM 出國服務。
視覺策略：機場、旅遊景點場景。手機螢幕顯示滿格訊號、地圖導航或 QR Code。強調國際感與便利。

MODE I：食品飲料 (Food & Beverage)
細分模式：
I-1 沖泡類：撕開包裝、倒入杯中、加熱水、攪拌。物理連續性必須符合重力邏輯。
I-2 即食/冷凍食品：冒煙的熱氣、豐富的肉汁、切割食物的斷面特寫。強調「縮短烹飪時間」。
I-3 休閒零食：居家放鬆或戶外野餐場景，強調享受瞬間。

- 嚴格遵守台灣，自動檢查《化妝品衛生安全管理法》與《健康食品管理法》。自動過濾任何醫療宣稱、前後對比或違法療效字眼。例如，將 "美白" 替換為 "Natural healthy complexion"。
- 若涉及版權特徵，僅以描述性特徵呈現（如："Red cap"），嚴禁直接提及品牌名稱或受版權保護的角色。

2) 腳本結構設計（15秒商業展示公式）：
- 0-3s 吸睛開場 (HOOK)：中景或半身吸睛開場，主角展現驚喜、滿意或自信表情，快速建立情緒與商品辨識度。內容需在 3 秒內抓住觀眾注意力。
- 3-9s 核心展示 (CORE)：特寫或穩定動態運鏡，商品佔畫面主體。展示產品材質、結構、細節、設計亮點或使用過程，嚴守物理邏輯與品類限制（如 3C 不插線、保健品不入口）。額外時長應用於提升商品展示完整性，而不是拖慢節奏。
- 9-15s 收尾推薦購買行動呼籲 (CTA)：中景，主角與產品同框，眼神直視鏡頭，動作自然穩定，預留後期壓字空間。CTA 依商品情境自然變動，例如：（一定要帶一罐啦、趕快趁優惠帶走、點連結包色吧，以上依商品情境變動相關語意）。

3) 視覺邏輯與人設規範：
- 智能選角系統 (Auto-Casting)：請根據產品屬性自動選擇最適合的主角性別。
  ▶ [女性預設] 若為通用商品、女裝、保養品：A stunning Taiwanese woman, age 21, celebrity model-level beauty, flawless natural skin, soft long flowing hair, refined light makeup, wearing a simple neutral-toned sleeveless basic top, high-end commercial style.
  ▶ [男性切換] 若為男裝、男性用品、強烈陽剛屬性產品：A trendy Taiwanese man, age 21, modern street fashion, stylish haircut, cool urban vibe, wearing high-quality simple outfit, street photography commercial style.
- 解剖學限制 (絕對強制，無論男女)：必須在人設後方緊接著寫入 "CRITICAL ANATOMY: Exactly ONE human, TWO arms, 5 fingers per hand"，嚴禁多肢或浮空手部。
- 場景規範：將私密場景如 "Bedroom" 自動替換為 "Bright Living Room"。

4) 音訊腳本 (Audio Spec)：
- 語言：繁體中文，具備台灣在地口語風格（如："欸！真的推欸"）。
- 長度：總字數嚴格限制在 40 到 55 字之間，配合 15 秒影片總長度的自然口語語速。
- 內容結構分配（需完美契合視覺時間軸）：
  1. 開場痛點與鉤子 (約 10-15 字)：配合 0-3s 畫面，精準點出痛點或驚喜感，快速抓眼球（例：「最近換季，狀態是不是超容易崩潰？」）。
  2. 核心亮點與體驗 (約 20-25 字)：配合 3-9s 畫面，嚴守法規，用朋友分享的口吻強調商品特色、質地或生活儀式感（例：「這款真的超有感！質地超水潤，輕輕一抹就吸收，出門準備超省時！」）。
  3. 行動呼籲 CTA (約 10-15 字)：配合 9-15s 畫面，語氣歡快具感染力，引導下一步動作（例：「現在買超划算，快點底下連結帶回家啦！」）。
- 智能配音選擇：若為女性角色，使用「Female voiceover in Mandarin...」；若判斷為男性角色，切換為「Natural Taiwanese male voice, young adult tone, calm, confident...」。
- 句型要求：必須精簡、清楚、好唸，絕對避免過長複句、過多規格堆疊、過多英文夾雜與拗口詞。
- 錄音品質：優先確保發音穩定、語意清楚、節奏自然，讓口播能剛好無縫貼合 15 秒影片長度。

5) 確保商品細節呈現完整性，商品對焦清晰：
- 商品必須在整段影片中維持主體辨識度，作為畫面主要視覺重心，禁止無意義弱化產品存在感。
- 商品特寫必須清楚呈現材質、結構、表面細節、使用狀態或設計亮點。
- 若為結構型、幾何型、3C 型或硬表面產品，必須維持原始比例、形體、表面細節與接口邏輯，不可產生變形、錯位、幻覺新增零件或不合理結構。
- 若為 Mode F 類產品，必須額外強化產品靜態精準度，避免任何不必要的產品位移、插線、接口誤生成或結構漂移。

6) 輸出格式要求：
- 格式必須嚴格依照以下順序：
MAIN CHARACTER:
SETTING ATMOSPHERE:
PRODUCT FOCUS:
VISUAL NARRATIVE TIMELINE:
AUDIO SPECIFICATION:
TECHNICAL REQUIREMENTS:（此區塊必須強制寫入以下防護參數："Photorealistic, cinematic style, 60fps, 15-second duration, clean commercial pacing, clear shot readability. CRITICAL: NO SUBTITLES, NO ON-SCREEN TEXT, NO WATERMARKS, NO UI ELEMENTS, NO SCREEN GRAPHICS."）

總體語氣：
專業、嚴謹且符合商業邏輯。確保最終輸出的英文指令包含 "Photorealistic, cinematic style, 60fps, 15-second duration, clean commercial pacing, clear shot readability, No subtitles, No watermarks" 等技術參數，並將額外時長用於提升商品細節展示完整性，而非拖慢節奏。避免 rushed motion、abrupt temporal jumps、unnecessary filler movement，確保每一段畫面都能清楚服務商品展示與商業轉化。
"""

@app.post("/api/generate")
async def generate_prompt(request: PromptRequest, token: str = Depends(verify_token)):
    """
    核心生成邏輯：透過 DEFAPI 呼叫 Gemini 3 Flash 模型進行視覺分析與腳本生成
    """
    if not request.gemini_api_key:
        raise HTTPException(status_code=400, detail="未提供 DEFAPI 金鑰")

    product = request.product_name
    img_url = request.image_url
    
    logger.info(f"收到請求 -> 準備處理商品: {product}")

    try:
        # 1. 抓取遠端圖片並轉換為 Base64 格式 (OpenAI Vision API 需求)
        logger.info("正在下載圖片並轉換為 Base64...")
        img_response = requests.get(img_url, timeout=15)
        img_response.raise_for_status()
        
        img_base64 = base64.b64encode(img_response.content).decode('utf-8')
        mime_type = img_response.headers.get('Content-Type', 'image/jpeg')
        image_data_url = f"data:{mime_type};base64,{img_base64}"

        # 2. 組合最終的請求指令
        final_prompt = (
            f"{SORA_SYSTEM_PROMPT}\n\n"
            f"現在，請根據這張圖片與產品名稱：「{product}」，"
            f"嚴格遵循上述所有規範，生成最終的 SORA 提示詞與音訊腳本。"
        )

# 3. 呼叫 DEFAPI (相容 OpenAI 格式) - 加入防彈重試機制
        logger.info("正在呼叫 DEFAPI (google/gemini-3-flash) 生成專業腳本...")
        defapi_url = "https://api.defapi.org/api/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {request.gemini_api_key}"
        }
        
        payload = {
            "model": "google/gemini-3-flash",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": final_prompt
                        },
                        {
                            "type": "image_url", 
                            "image_url": {
                                "url": image_data_url
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.7
        }

        # 設定最大重試次數
        max_retries = 3
        api_response = None
        
        import time # 確保開頭有 import time
        for attempt in range(max_retries):
            try:
                api_response = requests.post(defapi_url, headers=headers, json=payload, timeout=60)
                api_response.raise_for_status() # 如果是 200 就會順利往下走，如果是 500 就會跳到 except
                break # 成功了！跳出重試迴圈
                
            except requests.exceptions.HTTPError as e:
                # 如果是伺服器端錯誤 (500 開頭) 且還沒達到最大重試次數
                if e.response.status_code >= 500 and attempt < max_retries - 1:
                    logger.warning(f"⚠️ DEFAPI 伺服器不穩 (狀態碼: {e.response.status_code})，2 秒後進行第 {attempt + 2} 次重試...")
                    time.sleep(2) # 喘口氣等 2 秒
                    continue
                else:
                    raise # 如果不是 500 錯誤，或是重試 3 次都失敗，就真的報錯

        result_json = api_response.json()
        
        # 解析 OpenAI 格式的回傳內容
        generated_script = result_json['choices'][0]['message']['content'].strip()
        
        if not generated_script:
            raise ValueError("DEFAPI 模型回傳了空白結果")

        logger.info(f"✅ 腳本生成成功，長度: {len(generated_script)}")

        return {
            "success": True,
            "prompt": generated_script,
            "mode": "render_defapi_vision"
        }

    except Exception as e:
        logger.error(f"生成過程發生錯誤: {str(e)}")
        # 為了相容前端腳本的容錯處理，發生錯誤時回傳 false
        return {
            "success": False,
            "prompt": "",
            "error": {"message": str(e)}
        }

# ==========================================
# 💡 防休眠專屬小側門 (不需要 Token 驗證)
# ==========================================
@app.get("/keep-alive")
def keep_alive():
    import time
    now = time.time()
    return {"status": "alive", "service": "prompt-brain", "time": now}

# 讓 Render 能夠正確啟動
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)