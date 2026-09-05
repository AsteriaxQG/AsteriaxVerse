import data from '../../../data/changelog.json';
import {releases} from '../../../server/changelog.js';
export function onRequestGet() {
  return Response.json({versions:releases(data)},{headers:{'Cache-Control':'no-cache','X-Content-Type-Options':'nosniff'}});
}
