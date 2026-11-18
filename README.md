# YoloUNO IoT Gateway v0.2

Kiến trúc A:
- ESP32 -> Mosquitto local -> ThingsBoard IoT Gateway -> CoreIoT Cloud.
- Dashboard local -> Mosquitto local -> ESP32.
- CoreIoT RPC -> ThingsBoard IoT Gateway MQTT Connector -> Mosquitto -> ESP32.

ThingsBoard Gateway chính thức đảm nhiệm Cloud Bridge. Backend Python chỉ nhận telemetry để lưu SQLite và phục vụ Dashboard; không kết nối CoreIoT trực tiếp.


## 1. Chuẩn bị

Cài Docker Desktop trên Windows hoặc Docker Engine + Docker Compose trên Raspberry Pi/Linux.

Tạo file `.env` từ mẫu:

Windows PowerShell:
```powershell
Copy-Item .env.example .env
```

Linux/macOS:
```bash
cp .env.example .env
```

Mở `.env` và điền token mới của Gateway:
```env
COREIOT_GATEWAY_TOKEN=TOKEN_MOI
```

## 2. Khởi chạy

Từ thư mục chứa docker-compose.yml:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f tb-gateway
```

Dashboard:
- Trên máy Gateway: http://localhost:8000
- Từ máy khác trong LAN: http://IP_MAY_GATEWAY:8000

Mosquitto local: `IP_MAY_GATEWAY:1883`.

Lưu ý: Port 1883 trên PC/Raspberry Pi được Mosquitto chiếm. ThingsBoard Gateway và Dashboard truy cập broker bằng hostname nội bộ Docker `mosquitto`.

## 3. Cấu hình MQTT Connector trên CoreIoT

Sau khi container `tb-gateway` chạy và kết nối Cloud thành công:

1. Mở CoreIoT, vào Devices & assets / Gateways, chọn Gateway vừa tạo.
2. Mở Connectors configuration.
3. Add connector -> MQTT.
4. Trong Connection to broker:
   - Host: `mosquitto`
   - Port: `1883`
   - MQTT version: 3.1.1 hoặc 5 (chọn phiên bản được giao diện hỗ trợ)
   - Security: Anonymous (chỉ cho cấu hình LAN thử nghiệm hiện tại).
5. Trong Data mapping, thêm mapping:
   - Topic filter: `yolouno/+/telemetry`
   - QoS: `1`
   - Payload type: `JSON`
   - Device name source: `Topic`
   - Device name expression: `(?<=yolouno/)(.*?)(?=/telemetry)`
   - Device profile source: `Constant`
   - Device profile expression: `default` (hoặc tên Device Profile đã tạo trong CoreIoT).
   - Time series:
     - Key `temperature`, type `Double`, value `${temperature}`
     - Key `humidity`, type `Double`, value `${humidity}`
6. Save connector configuration. Gateway sẽ nhận cấu hình từ CoreIoT.

Nếu firmware gửi `temp`/`hum` thay vì `temperature`/`humidity`, đổi hai JSON path tương ứng trong connector hoặc thống nhất tên field trong firmware.

## 4. Cấu hình RPC từ CoreIoT xuống ESP32

Trong MQTT Connector -> Requests mapping -> Add mapping -> RPC command:

- Request type: `Without response` (One Way)
- Device name filter: `.*`
- Method filter: `setLedSwitchValue`
- Request topic expression: `yolouno/${deviceName}/command`
- Value expression: `{"method":"${methodName}","params":${params}}`

Lưu cấu hình. Khi gọi RPC trên thiết bị có tên đúng bằng `esp32_01`, ví dụ:
```json
{"method":"setLedSwitchValue","params":true}
```
Gateway publish lệnh lên topic:
`yolouno/esp32_01/command`

ESP32 cần subscribe topic này và xử lý JSON có hai trường `method`, `params`.

Nếu giao diện cấu hình RPC của phiên bản CoreIoT không chấp nhận biểu thức JSON ở Value expression, gửi ảnh màn hình phần RPC mapping để điều chỉnh đúng theo UI/phiên bản đang dùng.

## 5. Topic contract cho firmware ESP32

Device ID dùng làm tên thiết bị trên CoreIoT, ví dụ `esp32_01`.

Telemetry:
- Topic: `yolouno/esp32_01/telemetry`
- Payload:
```json
{"temperature":26.4,"humidity":58.1}
```

Status (tùy chọn):
- Topic: `yolouno/esp32_01/status`
- Payload:
```json
{"online":true}
```

Command:
- Subscribe: `yolouno/esp32_01/command`
- Payload:
```json
{"method":"setLedSwitchValue","params":true}
```

## 6. Test Mosquitto mà chưa cần sửa ESP32

Cài MQTT client `mosquitto_pub` hoặc dùng MQTT Explorer. Publish test từ máy có cài Mosquitto client:

```bash
mosquitto_pub -h IP_MAY_GATEWAY -p 1883 \
  -t yolouno/esp32_01/telemetry \
  -m '{"temperature":26.4,"humidity":58.1}'
```

Dashboard local sẽ ghi nhận thiết bị và dữ liệu. Sau khi cấu hình MQTT Connector, thiết bị `esp32_01` cũng sẽ được tạo/cập nhật trên CoreIoT.

Theo dõi log:
```bash
docker compose logs -f mosquitto
docker compose logs -f tb-gateway
docker compose logs -f dashboard
```

## 7. Giới hạn và bảo mật

- Mosquitto hiện bật anonymous để bring-up nhanh trong LAN. Không mở port 1883 ra Internet. Trước khi dùng thật, cấu hình username/password và ACL riêng cho thiết bị.
- Chỉ dùng `Without response` RPC ở giai đoạn đầu. Two-way RPC cần thiết kế thêm topic phản hồi và xử lý request ID ở firmware.
- Dashboard hiển thị telemetry khi Python backend nhận được bản tin MQTT. ThingsBoard Gateway độc lập subscribe cùng topic để chuyển telemetry lên Cloud.
- Cấu hình RPC, connector được lưu/quản lý bởi ThingsBoard Gateway/CoreIoT; không hardcode token CoreIoT vào mã Python.
