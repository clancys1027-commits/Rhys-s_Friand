```python                                                                       
  #!/usr/bin/env python3                                                        
  """                                                                           
  风切策略信号推送系统                                                          
  接收 TradingView webhook，解析信号并推送到 Telegram 群                        
  """                                                                           
                                                                                
  import json                                                                   
  import requests                                                               
  from http.server import HTTPServer, BaseHTTPRequestHandler                    
  from urllib.parse import urlparse                                             
                                                                                
  # Telegram Bot 配置（从环境变量读取，Render 上设置）                          
  import os                                                                     
  BOT_TOKEN = os.environ.get('BOT_TOKEN',                                       
'8737929922:AAFjQidOceYPjf5BILxfIV3sGr5xaPoB6as')                               
  CHAT_ID = os.environ.get('CHAT_ID', '-1003756244524')                         
  TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"                     
                                                                                
  # 文案模板                                                                    
  TEMPLATES = {                                                                 
      "warning": """⚡ *风切 · 预备*                                            
                                                                                
  系统监测到 BTC 15分钟周期上，{direction}力量已接近阶段性极限。                
  预备信号已触发，正在等待关键窗口确认。                                        
                                                                                
  密切关注下一个15分钟。""",                                                    
                                                                                
      "entry": """{emoji} *风切 · 确认*                                         
                                                                                
  {direction}力量衰竭已确认。系统判定这是值得关注的方向 性窗口。                
  信号强度：{grade_text}                                                        
                                                                                
  当前价格：{price}                                                             
  等待本窗口结算。                                                              
                                                                                
  _以上为系统策略记录，不构成投资建议。_""",                                    
                                                                                
      "result": """{emoji} *风切 · 结算*                                        
                                                                                
  方向：{direction}                                                             
  结果：{result_text}                                                           
  信号强度：{grade_text} 级                                                     
                                                                                
  统计数据已自动更新。                                                          
                                                                                
  _以上为系统策略记录，不构成投资建议。_"""                                     
  }                                                                             
                                                                                
                                                                                
  def send_telegram_message(text):                                              
      """发送消息到 Telegram"""                                                 
      url = f"{TELEGRAM_API}/sendMessage"                                       
      payload = {                                                               
          "chat_id": CHAT_ID,                                                   
          "text": text,                                                         
          "parse_mode": "Markdown"                                              
      }                                                                         
      try:                                                                      
          response = requests.post(url, json=payload, timeout=10)               
          result = response.json()                                              
          if result.get("ok"):                                                  
              print(f"✅ 消息发送成功: {result['result']['message_id']} ")      
              return True                                                       
          else:                                                                 
              print(f"❌ 发送失败: {result}")                                   
              return False                                                      
      except Exception as e:                                                    
          print(f"❌ 请求异常: {e}")                                            
          return False                                                          
                                                                                
                                                                                
  def format_direction(type_str):                                               
      """格式化方向"""                                                          
      return "多头" if type_str == "BUY" else "空头"                            
                                                                                
                                                                                
  def format_emoji(type_str):                                                   
      """格式化 emoji"""                                                        
      return "🟢" if type_str == "BUY" else "🔴"                                
                                                                                
                                                                                
  def format_grade(grade):                                                      
      """格式化信号强度"""                                                      
      grade_map = {                                                             
          "S": "⭐ S级·强",                                                     
          "A": "✅ A级·标准",                                                   
          "B": "💤 B级·弱"                                                      
      }                                                                         
      return grade_map.get(grade, grade)                                        
                                                                                
                                                                                
  def format_result(result):                                                    
      """格式化结果"""                                                          
      if result == "FAIL":                                                      
          return "❌ 窗口内未兑现"                                              
      elif result in ["WIN_1", "WIN_2", "WIN_3"]:                               
          return "✅ 窗口内方向兑现"                                            
      return result                                                             
                                                                                
                                                                                
  def process_signal(data):                                                     
      """处理信号数据并发送消息"""                                              
      stage = data.get("stage")                                                 
      type_str = data.get("type")                                               
      grade = data.get("grade")                                                 
      price = data.get("price", "N/A")                                          
      result = data.get("result")                                               
                                                                                
      print(f"📊 收到信号: stage={stage}, type={type_str}, grade={grade}")      
                                                                                
      # 构建变量                                                                
      direction = format_direction(type_str)                                    
      emoji = format_emoji(type_str)                                            
      grade_text = format_grade(grade)                                          
                                                                                
      # 根据阶段选择模板                                                        
      if stage == "warning":                                                    
          text = TEMPLATES["warning"].format(dire ction=direction)              
      elif stage == "entry":                                                    
          text = TEMPLATES["entry"].format(                                     
              emoji=emoji,                                                      
              direction=direction,                                              
              grade_text=grade_text,                                            
              price=price                                                       
          )                                                                     
      elif stage == "result":                                                   
          result_text = format_result(result)                                   
          text = TEMPLATES["result"].format(                                    
              emoji=emoji,                                                      
              direction=direction,                                              
              result_text=result_text,                                          
              grade_text=grade_text                                             
          )                                                                     
      else:                                                                     
          print(f"❌ 未知的 stage: {stage}")                                    
          return False                                                          
                                                                                
      # 发送消息                                                                
      return send_telegram_message(text)                                        
                                                                                
                                                                                
  class WebhookHandler(BaseHTTPRequestHa ndler):                                
      """HTTP 请求处理器"""                                                     
                                                                                
      def log_message(self, format, *args):                                     
          """自定义日志"""                                                      
          print(f"[{self.log_date_time_str ing()}] {format % args}")            
                                                                                
      def do_POST(self):                                                        
          """处理 POST 请求"""                                                  
          parsed_path = urlparse(self.path)                                     
                                                                                
          # 只处理 /webhook/tv-signal 路径                                      
          if parsed_path.path != "/webhook/tv-signal":                          
              self.send_response(404)                                           
              self.end_headers()                                                
              self.wfile.write(b'{"error": "Not Found"}')                       
              return                                                            
                                                                                
          # 读取请求体                                                          
          content_length = int(self.headers.get('Content-Le ngth', 0))          
          body = self.rfile.read(content_length)                                
                                                                                
          try:                                                                  
              # 解析 JSON                                                       
              data = json.loads(body.decode('utf-8'))                           
              print(f"📥 收到 webhook: {json.dumps(data, ensure_ascii=False)}") 
                                                                                
              # 处理信号                                                        
              success = process_signal(data)                                    
                                                                                
              # 返回响应                                                        
              if success:                                                       
                  self.send_response(200)                                       
                  self.send_header('Content-Type', 'application/json')          
                  self.end_headers()                                            
                  self.wfile.write(b'{"status": "ok"}')                         
              else:                                                             
                  self.send_response(500)                                       
                  self.send_header('Content-Type', 'application/json')          
                  self.end_headers()                                            
                  self.wfile.write(b'{"status": "error"}')                      
                                                                                
          except json.JSONDecodeError as e:                                     
              print(f"❌ JSON 解析错误: {e}")                                   
              self.send_response(400)                                           
              self.send_header('Content-Type', 'application/json')              
              self.end_headers()                                                
              self.wfile.write(b'{"error": "Invalid JSON"}')                    
          except Exception as e:                                                
              print(f"❌ 处理错误: {e}")                                        
              self.send_response(500)                                           
              self.send_header('Content-Type', 'application/json')              
              self.end_headers()                                                
              self.wfile.write(json.dumps({"er ror": str(e)}).encode())         
                                                                                
      def do_GET(self):                                                         
          """处理 GET 请求（健康检查）"""                                       
          self.send_response(200)                                               
          self.send_header('Content-Type', 'application/json')                  
          self.end_headers()                                                    
          self.wfile.write('{"status": "running", "service":                    
"fengqie-signal"}'.encode('utf-8'))                                             
                                                                                
                                                                                
  def main():                                                                   
      """启动 webhook 服务器"""                                                 
      import os                                                                 
      port = int(os.environ.get('PORT', 8080))                                  
      server = HTTPServer(('0.0.0.0', port), WebhookHandler)                    
      print(f"🚀 风切策略信号推送系统已启动")                                   
      print(f"📡 Webhook URL: http://localhost:{port}/webhook/tv-signal")       
      print(f"💬 Telegram 群: {CHAT_ID}")                                       
      print(f"🛑 按 Ctrl+C 停止")                                               
      print("-" * 50)                                                           
                                                                                
      try:                                                                      
          server.serve_forever()                                                
      except KeyboardInterrupt:                                                 
          print("\n🛑 服务器已停止")                                            
          server.shutdown()                                                     
                                                                                
                                                                                
  if __name__ == "__main__":                                                    
      main()                                                                    
```                             
