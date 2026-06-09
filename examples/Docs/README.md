# Project One — documentation

Read these docs in order for the full path from a prepared SD image to a running demo and production autostart.

| #   | Document                                    | Purpose                                                                                            |
| --- | ------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| 0   | [Image preparation](0_Image_preparation.md) | Rebuild the **prepared `.img`**: Python 3.11, venv, CSI, Docker, pre-pulled containers             |
| 1   | [Architecture](1_Architecture.md)           | How the repo is structured (`RPi/`, inputs, models, UI, hardware)                                  |
| 2   | [Kickoff](2_Kickoff.md)                     | **Project One: Getting Started**: flash image, SSH, clone repo, Gradio, Docker, coding tasks, demo |
| 3   | [Next steps](3_Next_steps.md)               | Home Wi‑Fi, laptop training, `RPi/ai/best.pt`, extend Gradio and hardware                          |
| 4   | [Production](4_Production.md)               | Autostart with systemd, test on **Wi‑Fi IP** (not only `192.168.168.167`)                          |
| —   | [Feedforward](Feedforward.md)               | Feedback conversation templates                                                                    |
| —   | [Appendix](Appendix.md)                     | Upgrades, GPIO fixes, port forwarding, optional extras                                             |
| —   | [RPi/docs/hardware-extensions.md](../RPi/docs/hardware-extensions.md) | Buzzer, 7-segment, NeoPixel (`pi5-neo`) — extend beyond kickoff |

**Kickoff image:** We distribute a prepared `.img` with the stack from doc **0** already applied. Flash that image, then follow doc **2**.

**Project definition:** [PD.md](../PD.md) in the repo root.
