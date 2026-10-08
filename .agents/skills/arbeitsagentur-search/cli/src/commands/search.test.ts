import {test, expect, spyOn} from 'bun:test'
import {runSearch} from './search'
test('finds fresh Airbus thesis after a full stale first page; requests broad date bucket',async()=>{
 const oldFetch=globalThis.fetch
 const urls:string[]=[]
 const today=new Date().toISOString().slice(0,10)
 const stale=Array.from({length:30},(_,i)=>({referenznummer:String(i),stellenangebotsTitel:'Old',firma:'X',datumErsteVeroeffentlichung:'2000-01-01'}))
 globalThis.fetch=(async (url:any)=>{
  urls.push(String(url));return new Response(JSON.stringify({ergebnisliste:urls.length===1?stale:[{referenznummer:'airbus',stellenangebotsTitel:'Master Thesis in Artificial Intelligence Organization Adoption and Usage',firma:'Airbus',datumErsteVeroeffentlichung:today}]}))
 }) as any
 const write=spyOn(process.stdout,'write').mockImplementation(()=>true)
 try {
  await runSearch({query:'Artificial Intelligence',limit:10,jobage:2})
  const data=JSON.parse(String(write.mock.calls[0][0]))
  expect(data.results[0].id).toBe('airbus')
  expect(data.meta.pagesFetched).toBe(2)
  expect(new URL(urls[0]).searchParams.get('veroeffentlichtseit')).toBe('7')
 }finally{globalThis.fetch=oldFetch;write.mockRestore()}
})
