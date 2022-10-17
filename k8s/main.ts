import { Construct } from 'constructs';
import { App } from 'cdk8s';
import { PennLabsChart, ReactApplication, DjangoApplication, CronJob, RedisApplication } from '@pennlabs/kittyhawk';

const cronTime = require('cron-time-generator');

export class MyChart extends PennLabsChart {
  constructor(scope: Construct) {
    super(scope);

    const secret = "penn-mobile";
    const backendImage = "pennlabs/penn-mobile-backend"
    const frontendImage = "pennlabs/penn-mobile-frontend"

    new RedisApplication(this, 'redis', {});

    new DjangoApplication(this, 'celery', {
      deployment: {
        image: backendImage,
        secret,
        cmd: ['celery', '-A', 'pennmobile', 'worker', '-linfo'],
        secretMounts: [
          {
            name: "penn-mobile",
            subPath: "ios-key",
            mountPath: "/app/ios_key.p8",
          }
        ]
      },
      djangoSettingsModule: 'pennmobile.settings.production',
    });

    new DjangoApplication(this, 'django', {
      deployment: {
        image: backendImage,
        secret,
        replicas: 5,
      },
      domains: [
        { host: 'studentlife.pennlabs.org', isSubdomain: true, paths: ['/'] },
        { host: 'portal.pennmobile.org', isSubdomain: true, paths: ['/api', '/assets'] },
        { host: 'pennmobile.org', paths: ['/api', '/assets'] },
      ],
      djangoSettingsModule: 'pennmobile.settings.production',
    });

    new ReactApplication(this, 'react', {
      deployment: {
        image: frontendImage,
      },
      domain: {
        host: "portal.pennmobile.org",
        isSubdomain: true,
        paths: ['/']
      },
    });

    new CronJob(this, 'get-laundry-snapshots', {
      schedule: cronTime.every(15).minutes(),
      image: backendImage,
      secret,
      cmd: ["python", "manage.py", "get_snapshot"],
      env: [{ name: "DJANGO_SETTINGS_MODULE", value: "pennmobile.settings.production" }]
    });

    new CronJob(this, 'send-gsr-reminders', {
      schedule: "20,50 * * * *",
      image: backendImage,
      secret,
      cmd: ["python", "manage.py", "send_gsr_reminders"],
      env: [{ name: "DJANGO_SETTINGS_MODULE", value: "pennmobile.settings.production" }]
    });

    new CronJob(this, 'get-fitness-snapshot', {
      schedule: cronTime.every(3).hours(),
      image: backendImage,
      secret,
      cmd: ["python", "manage.py", "get_fitness_snapshot"],
      env: [{ name: "DJANGO_SETTINGS_MODULE", value: "pennmobile.settings.production" }]
    });

    new CronJob(this, 'load-dining-menus', {
      schedule: cronTime.everyDay(),
      image: backendImage,
      secret,
      cmd: ["python", "manage.py", "load_next_menu"],
      env: [{ name: "DJANGO_SETTINGS_MODULE", value: "pennmobile.settings.production" }]
    });

  }
}

const app = new App();
new MyChart(app);
app.synth();
