import { App } from "cdkactions";
import { LabsApplicationStack } from "@pennlabs/kraken";

const app = new App();
new LabsApplicationStack(app, {
  djangoProjectName: 'pennmobile',
  dockerImageBaseName: 'penn-mobile',
  djangoCheckProps: {
    pythonVersion: "3.11-bookworm",
  }
});

app.synth();
