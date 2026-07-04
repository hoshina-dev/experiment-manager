import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://experiment-manager:8000";

function uuidv4() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function jsonHeaders() {
  return { headers: { "Content-Type": "application/json" } };
}

function questionDefault(question) {
  if (question.config && question.config.default !== undefined) {
    return question.config.default;
  }

  switch (question.type) {
    case "number":
      return 1;
    case "boolean":
      return false;
    case "select":
    case "string":
    case "text":
      return `load-test-${__VU}-${__ITER}`;
    default:
      return "";
  }
}

function collectDefaults(form) {
  const values = {};
  for (const question of form.questions || []) {
    values[question.id] = questionDefault(question);
  }
  return values;
}

export const options = {
  stages: [
    { duration: "15s", target: 5 },
    { duration: "45s", target: 15 },
    { duration: "30s", target: 25 },
    { duration: "15s", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.1"],
    http_req_duration: ["p(95)<3000"],
  },
};

export function setup() {
  let samplesRes;
  for (let i = 0; i < 60; i++) {
    samplesRes = http.get(`${BASE_URL}/api/samples`);
    if (samplesRes.status === 200) {
      break;
    }
    sleep(1);
  }

  if (!samplesRes || samplesRes.status !== 200) {
    throw new Error("experiment-manager not ready");
  }

  const samples = samplesRes.json().samples;
  const sample = samples.find((item) => item.name === "Coal") || samples[0];
  if (!sample) {
    throw new Error("no samples available for load test");
  }

  const templatesRes = http.get(`${BASE_URL}/api/samples/${sample.id}/experiments`);
  if (templatesRes.status !== 200) {
    throw new Error(`failed to load templates: ${templatesRes.status}`);
  }

  const templates = templatesRes.json().experiments;
  const template =
    templates.find((item) => item.name.includes("Calorific")) ||
    templates.find((item) => item.name.includes("Heat Capacity")) ||
    templates[0];
  if (!template) {
    throw new Error("no experiment templates available for load test");
  }

  const pdfTemplateRes = http.get(
    `${BASE_URL}/api/samples/${sample.id}/experiments/${template.id}/pdf`,
  );

  return {
    sampleID: sample.id,
    lineageID: template.lineage_id,
    templateID: template.id,
    hasPdfTemplate: pdfTemplateRes.status === 200,
  };
}

export default function (data) {
  const samplesRes = http.get(`${BASE_URL}/api/samples`);
  check(samplesRes, { "list samples": (r) => r.status === 200 });

  const templatesRes = http.get(`${BASE_URL}/api/samples/${data.sampleID}/experiments`);
  check(templatesRes, { "list templates": (r) => r.status === 200 });

  const templateRes = http.get(
    `${BASE_URL}/api/samples/${data.sampleID}/experiments/${data.templateID}`,
  );
  check(templateRes, { "get template": (r) => r.status === 200 });

  const expID = uuidv4();
  const createRes = http.post(
    `${BASE_URL}/api/experiments`,
    JSON.stringify({
      exp_id: expID,
      sample_id: data.sampleID,
      lineage_id: data.lineageID,
    }),
    jsonHeaders(),
  );
  check(createRes, { "create experiment": (r) => r.status === 201 });

  if (createRes.status !== 201) {
    sleep(0.5);
    return;
  }

  const experiment = createRes.json();

  const listRes = http.get(`${BASE_URL}/api/experiments`);
  check(listRes, { "list experiments": (r) => r.status === 200 });

  const getRes = http.get(`${BASE_URL}/api/experiments/${expID}`);
  check(getRes, { "get experiment": (r) => r.status === 200 });

  const values = Object.assign(
    {},
    collectDefaults(experiment.clientForm),
    collectDefaults(experiment.labForm),
  );
  const updateRes = http.put(
    `${BASE_URL}/api/experiments/${expID}`,
    JSON.stringify({
      clientForm: experiment.clientForm,
      labForm: experiment.labForm,
      calculations: experiment.calculations,
      values,
    }),
    jsonHeaders(),
  );
  check(updateRes, { "update experiment": (r) => r.status === 200 });

  const calculateRes = http.post(`${BASE_URL}/api/experiments/${expID}/calculate`);
  check(calculateRes, { "calculate experiment": (r) => r.status === 200 });

  if (data.hasPdfTemplate && __ITER % 10 === 0) {
    const reportRes = http.post(`${BASE_URL}/api/experiments/${expID}/report/generate`);
    check(reportRes, { "enqueue report": (r) => r.status === 202 });
  }

  sleep(0.2);
}
