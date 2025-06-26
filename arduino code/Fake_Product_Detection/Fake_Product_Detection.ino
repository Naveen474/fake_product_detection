#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);
const int buzzerPin = D6;

void setup() {
  Serial.begin(9600);
  lcd.init();
  lcd.backlight();
  pinMode(buzzerPin, OUTPUT);
  lcd.setCursor(0, 0);
  lcd.print("System Ready");
}

void loop() {
  if (Serial.available()) {
    String status = Serial.readStringUntil('\n');
    lcd.clear();
    if (status == "GENUINE") {
      lcd.setCursor(0, 0);
      lcd.print("Product Status:");
      lcd.setCursor(0, 1);
      lcd.print("GENUINE");
      digitalWrite(buzzerPin, LOW);
    } else if (status == "FAKE") {
      lcd.setCursor(0, 0);
      lcd.print("Product Status:");
      lcd.setCursor(0, 1);
      lcd.print("FAKE");
      tone(buzzerPin, 1000);
      delay(1000);
      noTone(buzzerPin);
    }
    delay(3000);
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("System Ready");
  }
}
