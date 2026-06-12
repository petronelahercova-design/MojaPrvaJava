import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner citac = new Scanner(System.in);
        
        // Táto premenná drží cyklus pri živote. Na začiatku je nastavená na "ano".
        String pokracovat = "ano"; 

        System.out.println("--- KALKULAČKA, KTORÁ NEKONČÍ ---");

        // CYKLUS: Bež dokola, pokiaľ je premenná pokracovat rovná "ano"
        while (pokracovat.equals("ano")) {

            System.out.println("\nZadaj prvé číslo:");
            double cislo1 = citac.nextDouble();

            System.out.println("Zadaj druhé číslo:");
            double cislo2 = citac.nextDouble();

            System.out.println("Zadaj tretie číslo:");
            double cislo3 = citac.nextDouble();

            System.out.println("Vyber si operáciu (+, -, /):");
            String operacia = citac.next();

            double vysledok = 0;

            if (operacia.equals("+")) {
                vysledok = cislo1 + cislo2 + cislo3;
            } else if (operacia.equals("-")) {
                vysledok = cislo1 - cislo2 - cislo3;
            } else if (operacia.equals("/")) {
                vysledok = cislo1 / (cislo2 + cislo3);
            }

            System.out.println("Výsledok: " + vysledok);

            // TU SA ROZHODNE O ĎALŠOM KOLE:
            System.out.println("\nChceš spočítať ďalší príklad? (napíš ano alebo nie):");
            pokracovat = citac.next(); // Ak napíšeš "nie", cyklus sa v ďalšom kole preruší
        }

        System.out.println("Ďakujem za použiie kalkulačky. Dovidenia!");
        citac.close();
    }
}