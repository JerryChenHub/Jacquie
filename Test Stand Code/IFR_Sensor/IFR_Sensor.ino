const int sensorPin = 6;
void setup() {
  pinMode(sensorPin, INPUT);
  Serial.begin(9600);

}

void loop() {
  int sensorValue = digitalRead(sensorPin);
  Serial.print("Sensor Value: ");
  Serial.println(sensorValue);
  delay(1000);
}
