# Home Assistant custom component: Balena Docker supervisor control

## 1. Background

### 1.1 What is Home Assistant?
[Home Assistant](https://www.home-assistant.io/) is an open-source home automation platform that runs locally and integrates with thousands of smart devices. You can extend it using [custom components](https://www.home-assistant.io/integrations/#custom-integrations), which let you add new device support, services, and automations beyond the built-in integrations.

### 1.2 What is Balena OS and the supervisor API?
[Balena OS](https://www.balena.io/os/) is a container-based operating system for IoT devices. It manages applications as Docker containers and provides device management features. The [Balena supervisor API](https://docs.balena.io/reference/supervisor/supervisor-api/) allows you to control containers and device configuration locally using HTTP endpoints.

## 2. Motivation

This project provides a custom Home Assistant component that lets you interact with containers running on your device using the Balena supervisor API. You can start, stop, and restart containers directly from Home Assistant, without needing Balena Cloud or the web dashboard.

## 3. How to install

### General instructions
See the [Home Assistant documentation on custom components](https://community.home-assistant.io/t/where-is-custom-components-folder/78438) and [serving local files (www)](https://developers.home-assistant.io/docs/frontend/custom-ui/registering-resources/). The configuration directory is the folder that contains the `configuration.yaml`.

### Steps

#### Manual Setup

1. Update your `docker-compose.yaml`, set `io.balena.features.supervisor-api: '1'` label to the home assistant container.

2. **Copy the custom component files:**
  - Copy the contents of the `custom_components/balena_docker` folder from this repository to `<config>/custom_components/balena_docker` in your Home Assistant configuration directory.

3. **Copy the frontend files:**
  - Copy the contents of the `www/balena_docker` folder to `<config>/www/balena_docker`.

4. **Update your `configuration.yaml`:**
  - Add the following to enable the integration:
    ```yaml
      # enable the custom_component (python backend)
      balena_docker:

      # load the javascript (frontend)
      lovelace:
        mode: yaml # the resources section below will only work if the mode is set to yaml (override the default UI mode).
        resources:
          - url: /local/balena_docker/more-info-balena_docker.js
            type: module
    ```
  - Restart Home Assistant to apply changes.

#### Scripted Setup
Depends on your usecase, you can create an script to automate the steps above, create your custom docker image that ship this componet on the go.
Rememer that symbolic links works in www and custom_component folder.

---

**Useful links:**
- [Home Assistant custom integrations guide](https://www.home-assistant.io/integrations/#custom-integrations)
- [Serving local files (www) in Home Assistant](https://www.home-assistant.io/integrations/frontend/#serving-local-files)
- [Balena supervisor API reference](https://docs.balena.io/reference/supervisor/supervisor-api/)

---

This component lets you control your device’s containers locally, making Home Assistant even more powerful for edge and IoT deployments.

