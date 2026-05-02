#include "HX711.h"
const int LOADCELL_DOUT_PIN=2;
const int LOADCELL_SCK_PIN=3;
double w1,k1,k2;
HX711 scale;

void setup() {
  Serial.begin(9600);
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  delay(1000);
}

void loop() {
  Serial.println("Remove all the load, press any key to continue");
  while(!Serial.available()){};
  Serial.read();
  k1=scale.get_units();
  
  Serial.println("Input and put the weight on it");
  while(!Serial.available()){
      w1= Serial.parseFloat();
  };
  k2=scale.get_units();
  
  Serial.print("w1:");
  Serial.println(w1);
  Serial.print("k1(bias):");
  Serial.println(k1);
  Serial.print("k2:");
  Serial.println(k2);
  Serial.print("(k2-k1)/w1 (lamda):");
  Serial.println((k2-k1)/w1);
  delay(2000);
}
