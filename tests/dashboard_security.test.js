const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, '../web/app.js'), 'utf8');

function helpers() {
  const context = { URL, Date, encodeURIComponent };
  vm.createContext(context);
  vm.runInContext(source.slice(source.indexOf('function safeExternalUrl')), context);
  return context;
}

test('external links reject executable and malformed protocols', () => {
  const { safeExternalUrl } = helpers();
  for (const value of ['javascript:alert(1)', 'data:text/html,script', 'file:///etc/hosts', '" onmouseover="alert(1)']) {
    assert.equal(safeExternalUrl(value), '#');
  }
  assert.equal(safeExternalUrl('https://example.com/jobs/1'), 'https://example.com/jobs/1');
});

test('PDF URLs stay within document routes and encode special characters', () => {
  const { documentUrl } = helpers();
  for (const value of ['//example.com/test.pdf', 'cv/../../private.pdf', '.env', 'javascript:alert(1)']) {
    assert.equal(documentUrl(value), '');
  }
  assert.match(documentUrl('documents/applications/Example_DataEngineer/a"b.pdf'), /^\/documents\/applications\/Example_DataEngineer\/a%22b\.pdf\?v=\d+$/);
});

test('actions retain metadata as data, including malicious quotes', () => {
  const context = helpers();
  const callbacks = {};
  const buttons = ['generate', 'status', 'cv', 'letter', 'contact', 'portal'].map(action => ({
    dataset: { action }, addEventListener: (_, callback) => { callbacks[action] = callback; }
  }));
  const captured = [];
  context.window = {
    generateDocuments: (...args) => captured.push(args),
    toggleAppliedStatus: (...args) => captured.push(args),
    viewPdf: (...args) => captured.push(args),
    editContactPerson: (...args) => captured.push(args),
    filterByPortal: (...args) => captured.push(args)
  };
  context.normalizePortalKey = () => 'linkedin';
  const hostile = 'Company" onpointerenter="alert(1)\\\'';
  context.bindRecordActions({ querySelectorAll: () => buttons }, { key: 'one', company: hostile, title: 'Data Engineer', status: 'new' });
  callbacks.generate();
  callbacks.status();
  assert.equal(captured[0][2], hostile);
  assert.equal(captured[1][1], hostile);
  assert.equal(captured[1][3], 'applied');
  assert.doesNotMatch(source, /onclick=/);
});


test('consolidated listings remain discoverable under all source portals', () => {
  const context = helpers();
  vm.runInContext(source.slice(source.indexOf('function normalizePortalKey'), source.indexOf('function formatPortalName')), context);
  assert.deepEqual(Array.from(context.jobPortalKeys({ portal: 'linkedin-search', portals: ['linkedin-search', 'freehire-search', 'linkedin-search'] })), ['linkedin', 'freehire']);
  assert.deepEqual(Array.from(context.jobPortalKeys({ portal: 'stepstone-search' })), ['stepstone']);
});
