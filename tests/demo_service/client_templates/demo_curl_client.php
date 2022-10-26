<?php

class DemoCurlClient extends TestClient {
    public function _dispatch(
        string $method,
        array $params,
        $converter_name
    ) {
        $port = intval(getenv('DEMO_SERVICE_PORT'));
        $host = '127.0.0.1';
        $url = "http://{$host}:{$port}/api.v1/call/{$method}";
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

        $data = json_decode($result, true);

        $ret = $this->{$converter_name}($data);
        return $ret;
    }
}
