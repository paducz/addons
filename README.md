# Audio Mixer with Ducking - Home Assistant Add-on

[![Open your Home Assistant instance and show the add-on store.](https://my.home-assistant.io/badges/supervisor_store.svg)](https://my.home-assistant.io/redirect/supervisor_store/)

Tento doplněk pro Home Assistant umožňuje dynamicky generovat profesionálně znějící zvukové soubory kombinací text-to-speech (TTS) od [ElevenLabs](https://elevenlabs.io/) a vaší vlastní hudby na pozadí.

Je navržen tak, aby byl plně ovladatelný z automatizací, což vám umožní vytvářet dynamická zvuková hlášení pro jakoukoliv událost ve vaší chytré domácnosti.

## Klíčové vlastnosti

-   **Dynamické generování řeči**: Používá špičkovou technologii od ElevenLabs pro převod textu na řeč.
-   **Hudba na pozadí**: Využívá jakýkoliv hudební soubor z vaší složky `/share`.
-   **Profesionální efekty**:
    -   **Intro**: Stopa začíná 1 sekundou samotné hudby.
    -   **Audio Ducking**: Hlasitost hudby se automaticky a plynule ztlumí, když zazní řeč.
    -   **Outro**: Po skončení řeči zazní ještě 1 sekunda hudby.
    -   **Fade-out**: Celá stopa na konci plynule zeslábne do ticha.
-   **Ovládání z automatizací**: Spouštějte generování zvuku pomocí služby `hassio.addon_stdin` a posílejte vlastní text, názvy souborů a další parametry přímo z vašich automatizací.

## Instalace

1.  Přejděte ve vašem Home Assistant do **Nastavení** > **Doplňky** > **Obchod s doplňky**.
2.  Klikněte na ikonu tří teček v pravém horním rohu a vyberte **Repozitáře**.
3.  Do pole "Přidat nový repozitář" vložte URL tohoto GitHub repozitáře a klikněte na **Přidat**.
4.  Zavřete okno pro správu repozitářů.
5.  Obnovte stránku obchodu (Ctrl+F5) a v nové sekci na stránce najděte doplněk "Audio Mixer with Ducking".
6.  Klikněte na doplněk a poté na **Nainstalovat**.

## Konfigurace

Po instalaci přejděte na kartu **Konfigurace**. Zde zadané hodnoty slouží jako **výchozí** pro případ, že je nepřepíšete v automatizaci.

| Volba               | Popis                                                                                              |
| ------------------- | -------------------------------------------------------------------------------------------------- |
| `elevenlabs_api_key`| **(Povinné)** Váš API klíč pro službu ElevenLabs.                                                  |
| `voice_id`          | ID hlasu, který chcete použít. ID naleznete v [Voice Lab](https://elevenlabs.io/voice-lab).         |
| `music_filename`    | Název vašeho hudebního souboru (např. `background.mp3`), který musí být umístěn ve složce `/share`. |
| `text_to_speak`     | Výchozí text, který se převede na řeč, pokud není specifikován v automatizaci.                     |
| `output_filename`   | Výchozí název výstupního souboru, který se uloží do složky `/share`.                               |

## Použití v automatizacích

Síla tohoto doplňku spočívá v jeho spouštění z automatizací pomocí služby `hassio.addon_stdin`. Tímto způsobem můžete dynamicky měnit, co se má říct a jak se má výstupní soubor jmenovat.

### Základní příklad

Tato automatizace vygeneruje soubor `welcome_home.mp3`, když se otevřou vchodové dveře.

```yaml
alias: "Generuj uvítací zprávu"
trigger:
  - platform: state
    entity_id: binary_sensor.vchodove_dvere # Upravte na váš senzor
    to: 'on'
action:
  - service: hassio.addon_stdin
    data:
      addon: "mix_audio_ducking" # Slug doplňku
      input:
        text_to_speak: "Vítejte doma. Doufám, že jste měli příjemný den."
        output_filename: "welcome_home.mp3"