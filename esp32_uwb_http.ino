/*
For ESP32 UWB AT Demo
Modified to send UWB data to API via HTTP.
*/

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

HardwareSerial mySerial2(2);

#define RESET 16
#define IO_RXD2 18
#define IO_TXD2 17
#define I2C_SDA 39
#define I2C_SCL 38

Adafruit_SSD1306 display(128, 64, &Wire, -1);

// Configurações Wi-Fi
const char* ssid = "SEU_SSID_WIFI"; // <<<<<<< SUBSTITUA PELO SEU SSID DO WI-FI
const char* password = "SUA_SENHA_WIFI"; // <<<<<<< SUBSTITUA PELA SUA SENHA DO WI-FI

// Configurações da API
// IMPORTANTE: Substitua pela URL da sua API no Render após o deploy
const char* API_URL = "https://sua-api-uwb.onrender.com/api/uwb/data"; // <<<<<<< SUBSTITUA PELA URL DA SUA API
const char* HEALTH_URL = "https://sua-api-uwb.onrender.com/api/uwb/health"; // <<<<<<< SUBSTITUA PELA URL DA SUA API

// Para testes locais, use:
// const char* API_URL = "http://192.168.1.100:5000/api/uwb/data"; // IP do seu computador na rede local
// const char* HEALTH_URL = "http://192.168.1.100:5000/api/uwb/health";

HTTPClient http;
WiFiClient client;

void connectWiFi() {
    Serial.print("Conectando ao Wi-Fi");
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("");
    Serial.println("Wi-Fi conectado!");
    Serial.print("Endereço IP: ");
    Serial.println(WiFi.localIP());
}

bool testAPIConnection() {
    Serial.print("Testando conexão com a API...");
    
    http.begin(client, HEALTH_URL);
    http.addHeader("Content-Type", "application/json");
    
    int httpResponseCode = http.GET();
    
    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.println("API está funcionando!");
        Serial.println("Resposta: " + response);
        http.end();
        return true;
    } else {
        Serial.print("Erro na conexão com a API: ");
        Serial.println(httpResponseCode);
        http.end();
        return false;
    }
}

void setup()
{
    pinMode(RESET, OUTPUT);
    digitalWrite(RESET, HIGH);

    Serial.begin(115200);

    Serial.print(F("Hello! ESP32-S3 AT command V1.0 Test"));
    mySerial2.begin(115200, SERIAL_8N1, IO_RXD2, IO_TXD2);

    mySerial2.println("AT");
    Wire.begin(I2C_SDA, I2C_SCL);
    delay(1000);
    
    // SSD1306_SWITCHCAPVCC = generate display voltage from 3.3V internally
    if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C))
    { // Address 0x3C for 128x32
        Serial.println(F("SSD1306 allocation failed"));
        for (;;)
            ; // Don't proceed, loop forever
    }
    display.clearDisplay();

    logoshow();

    connectWiFi();
    
    // Testar conexão com a API
    if (testAPIConnection()) {
        Serial.println("Sistema pronto para enviar dados UWB!");
    } else {
        Serial.println("AVISO: Não foi possível conectar à API. Verifique a URL e a conexão.");
    }
}

long int runtime = 0;

String response = "";
String rec_head = "AT+RANGE";

void loop()
{
    // put your main code here, to run repeatedly:
    while (Serial.available() > 0)
    {
        mySerial2.write(Serial.read());
        yield();
    }
    while (mySerial2.available() > 0)
    {
        char c = mySerial2.read();

        if (c == '\r')
            continue;
        else if (c == '\n' || c == '\r')
        {
            if (response.indexOf(rec_head) != -1)
            {
                range_analy(response);
            }
            else
            {
                Serial.println(response);
            }
            response = "";
        }
        else
            response += c;
    }

    // Verificar conexão Wi-Fi e reconectar se necessário
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("Wi-Fi desconectado. Tentando reconectar...");
        connectWiFi();
    }
}

// SSD1306
void logoshow(void)
{
    display.clearDisplay();
    display.setTextSize(2);              // Normal 1:1 pixel scale
    display.setTextColor(SSD1306_WHITE); // Draw white text
    display.setCursor(0, 0);             // Start at top-left corner
    display.println(F("UWB HTTP"));
    display.setCursor(0, 20);
    display.println(F("API"));
    display.setCursor(0, 40);
    display.println(F("Ready"));
    display.display();
    delay(2000);
}

bool sendDataToAPI(String tag_id, int range_values[8]) {
    // Criar JSON para enviar à API
    DynamicJsonDocument doc(1024);
    doc["id"] = tag_id;
    
    JsonArray range_array = doc.createNestedArray("range");
    for (int i = 0; i < 8; i++) {
        range_array.add(range_values[i]);
    }
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    Serial.print("Enviando para API: ");
    Serial.println(jsonString);
    
    // Fazer requisição HTTP POST
    http.begin(client, API_URL);
    http.addHeader("Content-Type", "application/json");
    
    int httpResponseCode = http.POST(jsonString);
    
    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.print("Resposta da API (código ");
        Serial.print(httpResponseCode);
        Serial.print("): ");
        Serial.println(response);
        
        // Verificar se foi sucesso (código 201)
        if (httpResponseCode == 201) {
            Serial.println("✓ Dados enviados com sucesso para a API!");
            http.end();
            return true;
        } else {
            Serial.println("✗ API retornou erro");
            http.end();
            return false;
        }
    } else {
        Serial.print("✗ Erro na requisição HTTP: ");
        Serial.println(httpResponseCode);
        http.end();
        return false;
    }
}

// AT+RANGE=tid:1,mask:04,seq:63,range:(0,0,0,0,0,0,0,0),rssi:(0.00,0.00,-77.93,0.00,0.00,0.00,0.00,0.00)
void range_analy(String data)
{
    String id_str = data.substring(data.indexOf("tid:") + 4, data.indexOf(",mask:"));
    String range_str = data.substring(data.indexOf("range:"), data.indexOf(",rssi:"));

    int range_list[8];
    int count = 0;

    count = sscanf(range_str.c_str(), "range:(%d,%d,%d,%d,%d,%d,%d,%d)",
                   &range_list[0], &range_list[1], &range_list[2], &range_list[3],
                   &range_list[4], &range_list[5], &range_list[6], &range_list[7]);

    if (count != 8)
    {
        Serial.println("RANGE ANALY ERROR");
        Serial.println(count);
        return;
    }

    // Serial Port Json (mantido para depuração local)
    String json_str = "";
    json_str = json_str + "{\"id\":" + id_str + ",";
    json_str = json_str + "\"range\":[";
    for (int i = 0; i < 8; i++)
    {
        if (i != 7)
            json_str = json_str + range_list[i] + ",";
        else
            json_str = json_str + range_list[i] + "]}";
    }
    Serial.println("Dados UWB locais: " + json_str);

    // Enviar dados para a API
    if (WiFi.status() == WL_CONNECTED) {
        bool success = sendDataToAPI(id_str, range_list);
        
        if (success) {
            // Atualizar display com sucesso
            display.clearDisplay();
            display.setTextSize(1);
            display.setTextColor(SSD1306_WHITE);
            display.setCursor(0, 0);
            display.println("Tag: " + id_str);
            display.setCursor(0, 10);
            display.println("Status: ENVIADO");
            display.setCursor(0, 20);
            display.println("API: OK");
            display.setCursor(0, 30);
            display.print("Range: ");
            display.print(range_list[0]);
            display.print(",");
            display.print(range_list[1]);
            display.print(",");
            display.print(range_list[2]);
            display.display();
        } else {
            // Atualizar display com erro
            display.clearDisplay();
            display.setTextSize(1);
            display.setTextColor(SSD1306_WHITE);
            display.setCursor(0, 0);
            display.println("Tag: " + id_str);
            display.setCursor(0, 10);
            display.println("Status: ERRO");
            display.setCursor(0, 20);
            display.println("API: FALHA");
            display.display();
        }
    } else {
        Serial.println("✗ Wi-Fi desconectado. Dados não enviados.");
        
        // Atualizar display com erro de Wi-Fi
        display.clearDisplay();
        display.setTextSize(1);
        display.setTextColor(SSD1306_WHITE);
        display.setCursor(0, 0);
        display.println("Tag: " + id_str);
        display.setCursor(0, 10);
        display.println("Status: ERRO");
        display.setCursor(0, 20);
        display.println("WiFi: DESCONECTADO");
        display.display();
    }
}

