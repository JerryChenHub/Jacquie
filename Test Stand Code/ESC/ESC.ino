#include <Servo.h>

Servo esc;

void setup() {
  Serial.begin(9600); // Start serial communication
  esc.attach(7); // Attach ESC signal wire to pin 9
  esc.writeMicroseconds(1000); // Set initial throttle to minimum (1000µs)
  delay(2000); // Allow ESC to initialize
  Serial.println("Enter throttle value (1000-2000):");
}

void loop() {
  if (Serial.available()) {
    int throttle = Serial.parseInt(); // Read user input as an integer
    if (throttle >= 1000 && throttle <= 2000) {
      esc.writeMicroseconds(throttle); // Set throttle
      Serial.print("Throttle set to: ");
      Serial.println(throttle);
    } else {
      Serial.println("Invalid input. Enter a value between 1000 and 2000.");
    }
  }
}
