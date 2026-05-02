void setup() {
  Serial.begin(9600);
}

void loop() {
  int value = analogRead(A4);
  Serial.println(value);
  delay(200);
}