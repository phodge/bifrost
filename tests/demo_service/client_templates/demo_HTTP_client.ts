import {ClientBase} from './generated_methods';
import {ApiFailure} from './generated_methods';
import {ApiOutage} from './generated_methods';
import {ApiBroken} from './generated_methods';


export class DemoClient extends ClientBase {
  public constructor(public host: string, public port: number) {
    super();
  }

  public async dispatch(
    method: string,
    params: {[k: string]: any},
    converter: (result: any) => any,
  ): Promise<ApiFailure | any> {
    const base_url = `http://${this.host}:${this.port}`;
    const url = base_url + '/api.v1/call/' + method;
    let resp: undefined|Response = undefined;

    const p = fetch(url, {
      method: "POST",

      // TODO: finalise good cross-origin sample code
      // XXX: node-fetch types don't include `mode` or `credentials` or `cache`
      //mode: 'cors',
      //credentials: "include",
      //cache: "no-cache",

      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });

    try {
      resp = await p;
    } catch(e) {
      if (e instanceof Error) {
        if (e.message == "NetworkError when attempting to fetch resource.") {
          // TODO: test this code path
          return new ApiOutage(e.message);
        }

        // anything else becomes a system error
        // TODO: test this code path
        return new ApiBroken('System error: ' + e.message);
      }

      throw new Error(`Unexpected error type ${e}`)
    }

    if (resp.ok) {
        return converter(await resp.json());
    }

    // TODO: deal with other error conditions

    // TODO: handle different values of Response.type as per:
    // https://developer.mozilla.org/en-US/docs/Web/API/Response/type
    if (resp.type == "opaque") {
    }

    // TODO: proper error here
    let text: string = "";
    try {
      text = await resp.text();
    } catch(e) {
      text = '<no error text>';
    }
    const msg = `${resp.status} ${resp.statusText}: ${text}`;
    return new ApiBroken('Error making request: ' + msg);
  }
}
