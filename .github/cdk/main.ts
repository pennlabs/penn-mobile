import { Construct } from "constructs";
import { App, Stack, Workflow } from "cdkactions";
import { DeployJob, DjangoProject } from "@pennlabs/kraken";

export class MobileStack extends Stack {
  constructor(scope: Construct, name: string) {
    super(scope, name);
    const workflow = new Workflow(this, 'build-and-deploy', {
      name: 'Build and Deploy',
      on: 'push',
    });

    const mobileJob = new DjangoProject(workflow, {
      path: 'backend',
      projectName: 'pennmobile',
      imageName: 'penn-mobile-backend',
    });

    new DeployJob(workflow, {}, {
      needs: [mobileJob.publishJobId]
    });
  }
}

const app = new App();
new MobileStack(app, 'mobile');
app.synth();
