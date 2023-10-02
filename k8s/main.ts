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
        ],
        env: [
          { name: 'REDIS_URL', value: 'redis://penn-mobile-redis:6379' },
        ],
      },
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

    new CronJob(this, 'load-target-populations', {
      schedule: cronTime.everyYearIn(8),
      image: backendImage,
      secret,
      cmd: ["python", "manage.py", "load_target_populations"],
      env: [{ name: "DJANGO_SETTINGS_MODULE", value: "pennmobile.settings.production" }]
    });

    // TODO: remove this once we have a better way to do this
    new CronJob(this, 'reset-wharton-caching-1', {
      schedule: cronTime.everyYearIn(10, 2),
      image: backendImage,
      secret,
      cmd: ["python", "manage.py", "reset_wharton_caching", "1"],
      env: [{ name: "DJANGO_SETTINGS_MODULE", value: "pennmobile.settings.production" }]
    });

    new CronJob(this, 'reset-wharton-caching-2', {
      schedule: cronTime.everyYearIn(10, 3),
      image: backendImage,
      secret,
      cmd: ["python", "manage.py", "reset_wharton_caching", "2"],
      env: [{ name: "DJANGO_SETTINGS_MODULE", value: "pennmobile.settings.production" }]
    });

    new CronJob(this, 'reset-wharton-caching-3', {
      schedule: cronTime.everyYearIn(10, 4),
      image: backendImage,
      secret,
      cmd: ["python", "manage.py", "reset_wharton_caching", "3"],
      env: [{ name: "DJANGO_SETTINGS_MODULE", value: "pennmobile.settings.production" }]
    });

    new CronJob(this, 'reset-wharton-caching-4', {
      schedule: cronTime.everyYearIn(10, 5),
      image: backendImage,
      secret,
      cmd: ["python", "manage.py", "reset_wharton_caching", "4"],
      env: [{ name: "DJANGO_SETTINGS_MODULE", value: "pennmobile.settings.production" }]
    });

    new CronJob(this, 'reset-wharton-caching-5', {
      schedule: cronTime.everyYearIn(10, 6),
      image: backendImage,
      secret,
      cmd: ["python", "manage.py", "reset_wharton_caching", "5"],
      env: [{ name: "DJANGO_SETTINGS_MODULE", value: "pennmobile.settings.production" }]
    });

  }
}

const app = new App({recordConstructMetadata: false});
new MyChart(app);
app.synth();
