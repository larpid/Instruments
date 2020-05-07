On our measurement PC tango servers like these are run as linux systemd services, which needs a servicefile at /lib/systemd/system using our name scheme: peem-[tango-]<your-service-name>.service.
Services then start at system boot and can be controlled via systemctl commands. An example .service file for peem-tango-annealPS.service looks like this:

[Unit]
Description=Tango server to control power supply for annealing
After=multi-user.target peem-startTangoDB.service
Requires=peem-startTangoDB.service
Conflicts=getty@tty1.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/chamber7/spinpluspython/Instruments/EAPSTango.py 2845070119
StandardInput=tty-force
#StandardOutput=journal  # activate this to get python stdout output printed to systemctl status <service-name>.service
Restart=no  # tango already does a solid job of ensuring no server is shut down randomly, so if not proven otherwise an automatic restart is not needed for these servers

[Install]
WantedBy=multi-user.target
