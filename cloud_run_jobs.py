from google.cloud import run_v2
from google import auth


def run_job(job_name: str, vars: dict[str, str]):

    print(f"Running job {job_name} with vars {vars}")
    credentials, project_id = auth.default()
    client = run_v2.JobsClient(credentials=credentials)

    env = []
    for key, value in vars.items():
        env.append(run_v2.types.EnvVar(name=key, value=value))

    request = run_v2.RunJobRequest(
        name=job_name,
        overrides=run_v2.types.RunJobRequest.Overrides(
            container_overrides=[run_v2.types.RunJobRequest.Overrides.ContainerOverride(env=env)])
    )

    return client.run_job(request=request)
