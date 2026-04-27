#!/usr/bin/env python3
"""Müşteriye özel ESP32 config header üretir."""

from pathlib import Path
import argparse

TEMPLATE = '''#ifndef CUSTOMER_CONFIG_H
#define CUSTOMER_CONFIG_H

#define WIFI_SSID "{wifi_ssid}"
#define WIFI_PASSWORD "{wifi_password}"
#define SUPABASE_URL "{supabase_url}"
#define SUPABASE_ANON_KEY "{supabase_anon_key}"
#define DEVICE_ID "{device_id}"

#endif
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--customer", required=True)
    parser.add_argument("--wifi-ssid", required=True)
    parser.add_argument("--wifi-password", required=True)
    parser.add_argument("--supabase-url", required=True)
    parser.add_argument("--supabase-anon-key", required=True)
    parser.add_argument("--device-id", required=True)
    args = parser.parse_args()

    safe_name = args.customer.strip().lower().replace(" ", "_")
    out = Path("esp32") / f"customer_config_{safe_name}.h"
    out.write_text(
        TEMPLATE.format(
            wifi_ssid=args.wifi_ssid,
            wifi_password=args.wifi_password,
            supabase_url=args.supabase_url,
            supabase_anon_key=args.supabase_anon_key,
            device_id=args.device_id,
        ),
        encoding="utf-8",
    )
    print(f"Config üretildi: {out}")


if __name__ == "__main__":
    main()
