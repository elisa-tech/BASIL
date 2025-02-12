from io import StringIO
import csv
import json
import os
import sys
import yaml
from typing import List

currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.dirname(currentdir))

from db.models.sw_requirement import SwRequirementModel  # noqa E402
from db.models.user import UserModel  # noqa E402


class SPDXImportBase:

    GRAPH_KEY = "@graph"
    MANDATORY_FIELDS = []
    OPTIONAL_FIELDS = []
    DEFAULT_INDEXES = (-1, -1)
    DB_MODEL = None

    def filter_valid_configs(self, _configs: List[dict], _mandatory_fields: List[str]) -> List[dict]:
        """Filter a list of dictionary selecting only the one
        with mandatory fields populated

        :param _configs: List of dictionaries to analyze
        :param _mandatory_fields: List of mandatory fields that must be populated in each dict
        :return: List of dictionaries with mandatory fields populated
        """
        valid_configs = []
        # Extract valid configuration based on _columns
        for iConf in range(len(_configs)):
            is_valid = True
            for col in _mandatory_fields:
                if col not in _configs[iConf].keys():
                    is_valid = False
                    break
                else:
                    if str(_configs[iConf][col]).strip() in ['None', '']:
                        is_valid = False
                        break
            if is_valid:
                valid_configs.append(_configs[iConf])
        return valid_configs

    def JsonToSelect(self, file_content: str) -> List[dict]:
        """Read a JSON file and extract work items

        Work items can be identified as part of a list or in case of single work item
        directly as a dictionary

        :param file_content: Content of the json file
        :return: list of dictionaries with mandatory fields
        """
        ret = []
        try:
            json_content = json.loads(file_content)
        except Exception as e:
            print(f"Error: exception at getJsonRequirementsToSelect: {e}")
            return ret

        if isinstance(json_content, list):
            json_configs = json_content
        else:
            if isinstance(json_content, dict):
                json_configs = [json_content]

        ret = self.filter_valid_configs(json_configs, self.MANDATORY_FIELDS)
        return ret

    def CSVToSelect(self, file_content: str) -> List[dict]:
        """Extract list of work items from a csv file

        By default the columsn delimiter is set to ;

        :param file_content: Content of the csv file
        :return: list of dictionaries with mandatory fields
        """
        ret = []
        csv_rows = []
        f = StringIO(file_content)
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            csv_rows.append(row)

        # Init columns indexes
        col_indexes = [self.DEFAULT_INDEXES for col in self.MANDATORY_FIELDS]
        optional_indexes = [self.DEFAULT_INDEXES for col in self.OPTIONAL_FIELDS]

        # identify columns indexes
        for iRow in range(len(csv_rows)):
            for iCol in range(len(csv_rows[iRow])):
                for iIndex in range(len(col_indexes)):
                    if col_indexes[iIndex] == self.DEFAULT_INDEXES:
                        if str(csv_rows[iRow][iCol]).lower() == str(self.MANDATORY_FIELDS[iIndex]).lower():
                            col_indexes[iIndex] = (iRow, iCol)
                for jIndex in range(len(optional_indexes)):
                    if optional_indexes[jIndex] == self.DEFAULT_INDEXES:
                        if str(csv_rows[iRow][iCol]).lower() == str(self.OPTIONAL_FIELDS[jIndex]).lower():
                            optional_indexes[jIndex] = (iRow, iCol)

            if len([x for x in col_indexes if x == self.DEFAULT_INDEXES]) == 0:
                if len([y for y in optional_indexes if y == self.OPTIONAL_FIELDS]) == 0:
                    break

        # Check all columns has been identified
        if len([x for x in col_indexes if x == self.DEFAULT_INDEXES]):
            print("Error: unable to find the column headers")
            return []

        # Check all columns are at the same row
        for i in range(1, len(col_indexes)):
            if (col_indexes[i][0] != col_indexes[0][0]):
                print("Error: unable to find the column headers at same row")
                return []

        # Check validity of optional fields
        valid_optional_fields = True
        for i in range(len(optional_indexes)):
            if (optional_indexes[i][0] != col_indexes[0][0]):
                valid_optional_fields = False

        for iRow in range(col_indexes[0][0] + 1, len(csv_rows)):
            tmp = {}
            for iCol in range(len(self.MANDATORY_FIELDS)):
                tmp[self.MANDATORY_FIELDS[iCol]] = csv_rows[iRow][col_indexes[iCol][1]]
            if valid_optional_fields:
                for jCol in range(len(self.OPTIONAL_FIELDS)):
                    tmp[self.OPTIONAL_FIELDS[jCol]] = csv_rows[iRow][optional_indexes[jCol][1]]
            ret.append(tmp)
        ret = self.filter_valid_configs(ret, self.MANDATORY_FIELDS)
        return ret

    def YAMLToSelect(self, file_content) -> List[dict]:
        """Extract list of work items from a yaml file

        Work items can be identified as part of a list or in case of single work item
        directly as a dictionary

        :param file_content: Content of the csv file
        :return: list of dictionaries with mandatory fields
        """
        yaml_content = yaml.safe_load(file_content)
        yaml_configs = []

        if isinstance(yaml_content, list):
            yaml_configs = yaml_content
        else:
            if isinstance(yaml_content, dict):
                yaml_configs = [yaml_content]

        ret = self.filter_valid_configs(yaml_configs, self.MANDATORY_FIELDS)
        return ret

    def XlsxToSelect(self, file_content: str) -> List[dict]:
        """Extract list of work items from a JSON file generated reading it from react

        Example of expected JSON:
        [{"__EMPTY":"id","__EMPTY_1":"title","__EMPTY_2":"description"},
         {"__EMPTY":1,"__EMPTY_1":"req1","__EMPTY_2":"Software requirement description one"},
         {"__EMPTY":2,"__EMPTY_1":"req2","__EMPTY_2":"Software requirement description two"},
         {"__EMPTY":3,"__EMPTY_1":"req3","__EMPTY_2":"Software requirement description three"}]

        :param file_content: Content of the JSON file
        :return: list of dictionaries with mandatory fields
        """
        ret = []

        DEFAULT_INDEXES = (-1, "")  # differ from self.DEFAULT_INDEXES

        try:
            json_content = json.loads(file_content)
        except Exception as e:
            print(f"Error: exception at getXlsxRequirementsToSelect: {e}")
            return ret

        if not isinstance(json_content, list):
            print("Error: a list was expected")
            return ret

        # Init columns indexes
        col_indexes = [DEFAULT_INDEXES for col in self.MANDATORY_FIELDS]
        optional_indexes = [self.DEFAULT_INDEXES for col in self.OPTIONAL_FIELDS]

        # identify columns keys
        for iRow in range(len(json_content)):
            for iCol in json_content[iRow].keys():
                for iIndex in range(len(col_indexes)):
                    if col_indexes[iIndex] == DEFAULT_INDEXES:
                        if str(json_content[iRow][iCol]).lower() == str(self.MANDATORY_FIELDS[iIndex]).lower():
                            col_indexes[iIndex] = (iRow, iCol)
                for jIndex in range(len(optional_indexes)):
                    if optional_indexes[jIndex] == self.DEFAULT_INDEXES:
                        if str(json_content[iRow][iCol]).lower() == str(self.OPTIONAL_FIELDS[jIndex]).lower():
                            optional_indexes[jIndex] = (iRow, iCol)

            if len([x for x in col_indexes if x == self.DEFAULT_INDEXES]) == 0:
                if len([y for y in optional_indexes if y == self.OPTIONAL_FIELDS]) == 0:
                    break

        # Check all columns has been identified
        if len([x for x in col_indexes if x == self.DEFAULT_INDEXES]):
            print("Error: unable to find the column headers")
            return []

        # Check all columns are at the same row
        for i in range(1, len(col_indexes)):
            if (col_indexes[i][0] != col_indexes[0][0]):
                print("Error: unable to find the column headers at same row")
                return []

        # Check validity of optional fields
        valid_optional_fields = True
        for i in range(len(optional_indexes)):
            if (optional_indexes[i][0] != col_indexes[0][0]):
                valid_optional_fields = False

        for iRow in range(col_indexes[0][0] + 1, len(json_content)):
            tmp = {}
            for iCol in range(len(self.MANDATORY_FIELDS)):
                tmp[self.MANDATORY_FIELDS[iCol]] = json_content[iRow][col_indexes[iCol][1]]
            if valid_optional_fields:
                for jCol in range(len(self.OPTIONAL_FIELDS)):
                    tmp[self.OPTIONAL_FIELDS[jCol]] = json_content[iRow][optional_indexes[jCol][1]]
            ret.append(tmp)
        ret = self.filter_valid_configs(ret, self.MANDATORY_FIELDS)
        return ret


class SPDXImportSwRequirements(SPDXImportBase):

    MANDATORY_FIELDS = ["title", "description"]
    OPTIONAL_FIELDS = ["id"]
    DEFAULT_INDEXES = (-1, -1)
    DB_MODEL = SwRequirementModel

    def extractWorkItems(self, file_name: str, file_content: str) -> List[dict]:
        """Extract work items depending on the file_name extension

        :param file_name: Filename uploaded by the user
        :param file_content: Content of the file uploaded by the user
        :return: List of work items dictionaries
        """
        file_ext = file_name.split(".")[-1]
        work_items = []
        if "json" in file_ext:
            work_items += self.BasilJsonRequirementsToSelect(file_content)
            work_items += self.JsonToSelect(file_content)
            work_items += self.StrictDocJsonRequirementsToSelect(file_content)
        elif "yaml" in file_ext:
            work_items += self.YAMLToSelect(file_content)
        elif "csv" in file_ext:
            work_items += self.CSVToSelect(file_content)
        elif "xlsx" in file_ext:
            work_items += self.XlsxToSelect(file_content)
        return work_items

    def BasilJsonRequirementsToSelect(self, file_content: str) -> List[dict]:
        """Read a json file exported by a BASIL instance and
        return a list of dictionaries with requirements data
        That list will be used by the user to select which one to import

        :param file_content: content of the sbom file generated by a BASIL instance
        :return: list of dictionaries
        """
        ret = []

        try:
            json_content = json.loads(file_content)
        except Exception as e:
            print(f"Error: exception at getBasilSwRequirementsToSelect: {e}")
            return ret

        # Skip in case of not spdx json
        if not isinstance(json_content, dict):
            return ret
        if self.GRAPH_KEY not in json_content.keys():
            return ret

        spdx_files = [_file for _file in json_content[self.GRAPH_KEY] if _file["@type"] == "File"]
        spdx_sw_requirements = [_file for _file in spdx_files if _file["summary"] == self.DB_MODEL._description]
        for spdx_sw_requirement in spdx_sw_requirements:
            sr_data = json.loads(spdx_sw_requirement["attributionText"])
            # Check work item mandatory fields
            valid_data = True
            for data_field in self.MANDATORY_FIELDS:
                if data_field not in sr_data.keys():
                    valid_data = False
                    break

            if valid_data:
                ret.append(
                    {
                        "id": spdx_sw_requirement["@id"],
                        "title": sr_data["title"],
                        "description": sr_data["description"],
                    }
                )
        return ret

    def StrictDocJsonRequirementsToSelect(self, file_content: str) -> List[dict]:
        """Read an SPDX JSON file exported from StrictDoc and extract Requirement

        Stricdoct is defining requirements in Snippets using an identifier "Requirement"
        in the name field

        :param file_content: Content of the json file
        :return: list of dictionaries with mandatory fields
        """
        STRICTDOC_REQ_IDENTIFIER = "Requirement '"

        ret = []
        try:
            json_content = json.loads(file_content)
        except Exception as e:
            print(f"Error: exception at getStrictDocJsonRequirementsToSelect: {e}")
            return ret

        # Skip in case of not spdx json
        if not isinstance(json_content, dict):
            return ret
        if self.GRAPH_KEY not in json_content.keys():
            return ret

        spdx_snippets = [snippet for snippet in json_content[self.GRAPH_KEY] if snippet["@type"] == "Snippet"]
        spdx_sw_requirements = [req for req in spdx_snippets if req["name"].startswith(STRICTDOC_REQ_IDENTIFIER)]

        for spdx_req in spdx_sw_requirements:
            tmp = {
                "id": spdx_req["@id"],
                "title": spdx_req["name"].replace(STRICTDOC_REQ_IDENTIFIER, "").replace("'", ""),
                "description": spdx_req["description"]
            }
            ret.append(tmp)

        ret = self.filter_valid_configs(ret, self.MANDATORY_FIELDS)
        return ret

    def getFilteredSwRequirementModels(self, items: List[dict], user: UserModel) -> List[SwRequirementModel]:
        """Generate a list of Software Requirements models from list of dictionaries

        Validate that each items has all the mandatory fields populated

        :param items: list of dictionaries
        :param user: UserModel of who is importing the sw requirements
        :return: list of SwRequirementModels
        """
        sw_requirements = []
        sw_requirements_dict = self.filter_valid_configs(items, self.MANDATORY_FIELDS)
        for sw_requirement_dict in sw_requirements_dict:
            sw_requirements.append(
                    SwRequirementModel(title=sw_requirement_dict["title"],
                                       description=sw_requirement_dict["description"],
                                       created_by=user)
                )
        return sw_requirements
