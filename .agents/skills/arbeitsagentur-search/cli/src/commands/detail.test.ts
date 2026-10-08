import { expect, test } from 'bun:test'
import { externalJobUrls } from './detail'

test('keeps nested explicit referral URLs without treating prose as URLs', () => {
  expect(externalJobUrls({externeUrl:'https://careers.example/jobs/123',
    bewerbung:{links:[{url:'https://ats.example/job/123'}]},
    description:'https://not-a-link-field.example', invalidUrl:'javascript:alert(1)'}))
    .toEqual(['https://careers.example/jobs/123','https://ats.example/job/123'])
})
