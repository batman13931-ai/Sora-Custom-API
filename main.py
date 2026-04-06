"""
SORA 專屬提示詞生成 API (Render 部署版)
"""
import os
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

# 建立 FastAPI 應用
app = FastAPI(title="SORA Custom Prompt API")

# 定義接收的前端請求格式 (完美對接您的 generate_script.py)
class PromptRequest(BaseModel):
    image_url: str
    product_name: str
    action: str

# 安全防護：從環境變數讀取金鑰，預設為 test_token
API_TOKEN = os.environ.get("API_TOKEN", "test_token")

def verify_token(authorization: Optional[str] = Header(None)):
    """驗證請求是否帶有正確的 Bearer Token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少授權 Token 或格式錯誤")
    
    token = authorization.split(" ")[1]
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token 驗證失敗，無權限存取")
    return token

@app.post("/api/generate")
async def generate_prompt(request: PromptRequest, token: str = Depends(verify_token)):
    """
    核心生成邏輯：接收商品資訊，回傳 SORA 提示詞
    """
    product = request.product_name
    img_url = request.image_url
    
    print(f"收到請求 -> 商品: {product}, 圖片: {img_url}")

    # ==========================================
    # 這裡未來可以串接您自己的 AI (如 Gemini 或 OpenAI)
    # 目前先為您自動生成一組超高品質的 SORA 預設咒語模板
    # ==========================================
    
    generated_prompt = (
        f"A cinematic, 4k resolution, highly detailed video showcasing the product: {product}. "
        "The lighting is photorealistic with a studio setup, soft shadows, and a smooth camera pan. "
        "High quality, visually stunning, trending on artstation, 60fps."
    )
    
    # 回傳 JSON 格式必須與 generate_script.py 預期的一致
    return {
        "success": True,
        "prompt": generated_prompt,
        "mode": "custom_api_render"
    }

# 讓 Render 能夠正確啟動
if __name__ == "__main__":
    # Render 會自動分配 PORT 環境變數
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)