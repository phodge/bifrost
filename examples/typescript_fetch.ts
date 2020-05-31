import {YourGeneratedClient} from 'your_generated_module';
import {ApiFailure} from 'your_generated_module';
import {ApiOutage} from 'your_generated_module';
import {ApiBroken} from 'your_generated_module';

// re-export
export {ApiFailure};
export {ApiOutage};
export {ApiBroken};

// re-export types so everything can be imported from this module
export {YourNumberType} from 'your_generated_module';
export {YourDataclass} from 'your_generated_module';


export class CoolClient extends YourGeneratedClient {
  constructor(private base_url: string) {
    super();
  }

  public async dispatch(
    method: string,
    params: {[k: string]: any},
    converter: (result: any) => any,
  ): Promise<ApiFailure | any> {
    const url = this.base_url + '/api.v1/call/' + method;

    let resp: undefined|Response = undefined;

    const p = window.fetch(url, {
      method: "POST",

      // TODO: finalise good cross-origin sample code
      mode: 'cors',
      credentials: "include",

      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },

      cache: "no-cache",
      body: JSON.stringify(params),
    });

    try {
      resp = await p;
    } catch(e) {
      if (e.message == "NetworkError when attempting to fetch resource.") {
        return new ApiOutage(e.message);
      }

      // anything else becomes a system error
      return new ApiBroken('System error: ' + e.message);
    }

    if (resp.ok) {
        return converter(await resp.json());
    }

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
