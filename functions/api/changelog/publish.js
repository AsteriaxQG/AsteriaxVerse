import data from '../../../data/changelog.json';
import {publish} from '../../../server/changelog-publisher.js';
export const onRequest=({request,env})=>publish(request,env,data);
