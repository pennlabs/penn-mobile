import { Construct } from 'constructs';
import { App } from 'cdk8s';
import { PennLabsChart, ReactApplication, DjangoApplication, CronJob, RedisApplication } from '@pennlabs/kittyhawk';

const cronTime = require('cron-time-generator');

export class MyChart extends PennLabsChart {
  constructor(scope: Construct) {
    super(scope);

    const secret = "penn-mobile";
    const backendImage = "pennlabs/penn-mobile-backend";
    const frontendImage = "pennlabs/penn-mobile-frontend";
    const ingressProps = {
      annotations: {
        ["ingress.kubernetes.io/protocol"]: "https",
        ["traefik.ingress.kubernetes.io/router.middlewares"]: "default-redirect-http@kubernetescrd"
      }
    };

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
        ],
        env: [
          { name: 'REDIS_URL', value: 'redis://penn-mobile-redis:6379' },
        ],
      },
      ingressProps,
      djangoSettingsModule: 'pennmobile.settings.production',
    });

    new DjangoApplication(this, 'django', {
      deployment: {
        image: backendImage,
        secret,
        replicas: 1,
        secretMounts: [
          {
            name: "penn-mobile",
            subPath: "ios-key",
            mountPath: "/app/ios_key.p8",
          }
        ]
      },
      domains: [
        { host: 'studentlife.pennlabs.org', isSubdomain: true, paths: ['/'] },
        { host: 'portal.pennmobile.org', isSubdomain: true, paths: ['/api', '/assets'] },
        { host: 'pennmobile.org', paths: ['/api', '/assets'] },
      ],
      ingressProps,
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
      ingressProps,
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

    new CronJob(this, 'load-target-populations', {
      schedule: cronTime.everyYearIn(8),
      image: backendImage,
      secret,
      cmd: ["python", "manage.py", "load_target_populations"],
      env: [{ name: "DJANGO_SETTINGS_MODULE", value: "pennmobile.settings.production" }]
    });

    new CronJob(this, 'get-calendar', {
      schedule: '0 3 1 * *', // This expression means run at 3 AM on the 1st day of every month
      image: backendImage,
      secret,
      cmd: ["python", "manage.py", "get_calendar"],
      env: [{ name: "DJANGO_SETTINGS_MODULE", value: "pennmobile.settings.production" }]
    });

    new CronJob(this, 'get-penn-today-events', {
      schedule:'0 15 * * *', // Every day at 3 PM
      image: backendImage,
      secret,
      cmd: ["python", "manage.py", "get_penn_today_events"],
      env: [{ name: "DJANGO_SETTINGS_MODULE", value: "pennmobile.settings.production" }]
    });

    new CronJob(this, 'get-engineering-events', {
      schedule:'0 16 * * *', // Every day at 4 PM
      image: backendImage,
      secret,
      cmd: ["python", "manage.py", "get_engineering_events"],
      env: [{ name: "DJANGO_SETTINGS_MODULE", value: "pennmobile.settings.production" }]
    });

    new CronJob(this, 'get-venture-events', {
      schedule:'0 16 * * *', // Every day at 4 PM
      image: backendImage,
      secret,
      cmd: ["python", "manage.py", "get_venture_events"],
      env: [{ name: "DJANGO_SETTINGS_MODULE", value: "pennmobile.settings.production" }]
    });

    new CronJob(this, 'get-college-house-events', {
      schedule:'0 17 * * *', // Every day at 5 PM
      image: backendImage,
      secret,
      cmd: ["python", "manage.py", "get_college_house_events"],
      env: [{ name: "DJANGO_SETTINGS_MODULE", value: "pennmobile.settings.production" }]
    });
  }
}

const app = new App({recordConstructMetadata: false});
new MyChart(app);
app.synth();
