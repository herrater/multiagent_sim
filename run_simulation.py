#!/usr/bin/env python3
# run_simulations.py

import subprocess
import argparse
import re
import pandas as pd

def parse_collisions(output):

    ped_match = re.search(r"Liczba kolizji pieszych:\s*(\d+)", output)
    car_match = re.search(r"Liczba kolizji pojazdów:\s*(\d+)", output)

    if not ped_match or not car_match:
        raise ValueError("Nie udało się odczytać liczby kolizji z wyjścia symulacji.")
    return int(ped_match.group(1)), int(car_match.group(1))

def run_one(script_path):

    # python3 --unbuffered, aby od razu otrzymywać całe stdout
    proc = subprocess.run(
        ["python3", "-u", script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if proc.returncode != 0:
    
        raise RuntimeError(f"Symulacja zakończona błędem:\n{proc.stderr}")
    return proc.stdout

def main():
    parser = argparse.ArgumentParser(
        
    )
    parser.add_argument(
        "--script",
        "-s",
        required=True,
       
    )
    parser.add_argument(
        "--n",
        "-n",
        type=int,
        default=50,
        "
    )
    parser.add_argument(
        "--output",
        "-o",
        default="wyniki_symulacji.xlsx",
        
    )
    args = parser.parse_args()

    results = []
    for i in range(1, args.n + 1):
        print(f"Uruchamiam symulację {i}/{args.n}…", end=" ")
        try:
            out = run_one(args.script)
            ped, car = parse_collisions(out)
            results.append({"run": i, "collisions_ped": ped, "collisions_car": car})
            print(f"OK (piesi={ped}, pojazdy={car})")
        except Exception as e:
            print(f"\n[!] Błąd w symulacji {i}: {e}")
            # Możesz tu zdecydować, czy przerwać cały proces, czy pominąć tę paczkę:
            # raise
            continue

    if not results:
        print("Brak prawidłowych wyników – nic nie zapisano.")
        return

    # Tworzymy DataFrame i zapisujemy do Excela
    df = pd.DataFrame(results)
    # Kolumny: run, collisions_ped, collisions_car
    df.to_excel(args.output, index=False)
    print(f"\nZapisano wyniki do pliku: {args.output}")

if __name__ == "__main__":
    main()
