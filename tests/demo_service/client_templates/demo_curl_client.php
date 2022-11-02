<?php

class DemoCurlClient extends ClientBase {
    private $host;
    private $port;

    public function __construct($host, $port) {
        $this->host = $host;
        $this->port = $port;
    }

    public function _dispatch(
        string $method,
        array $params,
        $converter_name
    ) {
        $url = "http://{$this->host}:{$this->port}/api.v1/call/{$method}";
        $headers = [
            'Accept: application/json',
            'Content-Type: application/json',
        ];
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "POST");
        curl_setopt($ch, CURLOPT_HEADER, 0);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($params));
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        $result = curl_exec($ch);
        if ($result === false) {
            $err = curl_error($ch);
            throw new Exception("CURL ERROR: $err");
        }

        $info = curl_getinfo($ch);
        if ($info['http_code'] !== 200) {
            # TODO: test this code path when we rework errors
            return new ApiBroken("Unexpected HTTP {$info['http_code']} response from rpc server: {$result}");
        }

        // TODO: should return ApiBroken() when we don't get valid JSON back
        $data = json_decode($result, true);

        // TODO: should return ApiBroken() when the converter fails
        $ret = $this->{$converter_name}($data);
        return $ret;
    }
}
