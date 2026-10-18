import http from "http";

const options = {
  hostname: "127.0.0.1",
  port: 8000,
  path: "/api/v1/smoke-test/",
  method: "GET",
  headers: {
    Accept: "application/json",
  },
};

console.log("FutureLearning Smoke Test: Connecting to Django backend...");

const req = http.request(options, (res) => {
  let body = "";
  res.on("data", (chunk) => {
    body += chunk;
  });
  res.on("end", () => {
    try {
      const data = JSON.parse(body);
      console.log("\n=======================================================");
      console.log("FUTURELEARNING CROSS-SYSTEM PIPELINE VERIFICATION");
      console.log("=======================================================");
      console.log(`Test Name:       ${data.test_name}`);
      console.log(`Status Code:     ${res.statusCode}`);
      console.log(`All Passed:      ${data.all_passed}`);
      console.log(`Total Latency:   ${data.total_elapsed_ms} ms`);
      console.log("\nPipeline Steps:");
      console.log(`1. Django API:     ${data.pipeline["1_django_api"]?.status}`);
      console.log(`2. Neon Database:  ${data.pipeline["2_neon_postgres"]?.status} (${data.pipeline["2_neon_postgres"]?.database_name})`);
      console.log(`3. Redis Cache:    ${data.pipeline["3_redis_cache"]?.status}`);
      console.log(`4. Celery Worker:  ${data.pipeline["4_celery_task"]?.status}`);
      console.log("=======================================================\n");
      if (data.all_passed) {
        process.exit(0);
      } else {
        process.exit(1);
      }
    } catch (e) {
      console.error("Failed to parse response JSON:", body);
      process.exit(1);
    }
  });
});

req.on("error", (e) => {
  console.error(`Smoke test failed to connect: ${e.message}`);
  process.exit(1);
});

req.end();
