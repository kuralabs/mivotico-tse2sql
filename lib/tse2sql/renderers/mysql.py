# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2017 KuraLabs S.R.L
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
MySQL SQL generator.
"""

from logging import getLogger

from tqdm import tqdm


log = getLogger(__name__)


SCHEMA = """\
-- MySQL Script generated by MySQL Workbench
-- Thu 18 Feb 2016 02:05:16 AM CST
-- Model: TSE Voters MySQL Database    Version: 1.0
-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- -----------------------------------------------------
-- Schema tse2sql
-- -----------------------------------------------------
DROP SCHEMA IF EXISTS `tse2sql` ;

-- -----------------------------------------------------
-- Schema tse2sql
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `tse2sql` DEFAULT CHARACTER SET utf8 ;
USE `tse2sql` ;

-- -----------------------------------------------------
-- Table `tse2sql`.`province`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tse2sql`.`province` (
  `id_province` TINYINT(1) UNSIGNED NOT NULL,
  `name_province` VARCHAR(10) NOT NULL,
  PRIMARY KEY (`id_province`))
ENGINE = InnoDB
COMMENT = 'Costa Rica has 7 provinces, plus one code for consulates.';


-- -----------------------------------------------------
-- Table `tse2sql`.`canton`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tse2sql`.`canton` (
  `id_canton` SMALLINT(3) UNSIGNED NOT NULL,
  `name_canton` VARCHAR(20) NOT NULL,
  `province_id_province` TINYINT(1) UNSIGNED NOT NULL,
  PRIMARY KEY (`id_canton`, `province_id_province`),
  INDEX `fk_canton_province_idx` (`province_id_province` ASC),
  CONSTRAINT `fk_canton_province`
    FOREIGN KEY (`province_id_province`)
    REFERENCES `tse2sql`.`province` (`id_province`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = 'As of 02/2016 Costa Rica has 81 cantons (124 if including consulates).\nThe largest name was \"REPUBLICA DOMINICANA\" (20 characters).';


-- -----------------------------------------------------
-- Table `tse2sql`.`district`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tse2sql`.`district` (
  `id_district` MEDIUMINT(6) UNSIGNED NOT NULL,
  `name_district` VARCHAR(34) NOT NULL,
  `canton_id_canton` SMALLINT(3) UNSIGNED NOT NULL,
  `voting_center_name` TEXT NULL,
  `voting_center_address` TEXT NULL,
  `voting_center_latitude` DECIMAL(9,6) NULL,
  `voting_center_longitude` DECIMAL(9,6) NULL,
  PRIMARY KEY (`id_district`, `canton_id_canton`),
  INDEX `fk_district_canton_idx` (`canton_id_canton` ASC),
  CONSTRAINT `fk_district_canton`
    FOREIGN KEY (`canton_id_canton`)
    REFERENCES `tse2sql`.`canton` (`id_canton`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = 'As of 02/2016 Costa Rica has 2068 districts (2123 if including consulates).\nThe largest name was \"EMPALME ARRIBA GUARIA(PARTE OESTE)\" (34 characters).';


-- -----------------------------------------------------
-- Table `tse2sql`.`voter`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tse2sql`.`voter` (
  `id_voter` INT UNSIGNED NOT NULL,
  `sex` TINYINT(1) UNSIGNED NOT NULL,
  `id_expiration` DATE NOT NULL,
  `site` MEDIUMINT(5) UNSIGNED NOT NULL,
  `name` VARCHAR(30) NOT NULL,
  `family_name_1` VARCHAR(26) NOT NULL,
  `family_name_2` VARCHAR(26) NOT NULL,
  `district_id_district` MEDIUMINT(6) UNSIGNED NOT NULL,
  PRIMARY KEY (`id_voter`, `district_id_district`),
  INDEX `fk_voter_district_idx` (`district_id_district` ASC),
  FULLTEXT INDEX `full_name` (`name` ASC, `family_name_1` ASC, `family_name_2` ASC),
  CONSTRAINT `fk_voter_district`
    FOREIGN KEY (`district_id_district`)
    REFERENCES `tse2sql`.`district` (`id_district`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


"""  # noqa

SECTION_HEADER = """\
-- -----------------------------------------------------
-- Data for table `tse2sql`.`{name}`
-- -----------------------------------------------------
"""

FOOTER = """\
SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
"""


def write_provinces(fd, provinces):
    """
    Write provinces INSERT INTO statement.
    """
    opening_statement = (
        'SET AUTOCOMMIT=0;\n'
        'INSERT INTO `province` VALUES\n'
    )

    fd.write(SECTION_HEADER.format(name='province'))
    fd.write(opening_statement)

    with tqdm(
            total=len(provinces), unit='e', leave=True,
            desc='INSERT INTO province') as pbar:

        for province_code, name in provinces.items():
            fd.write('(')
            fd.write(str(province_code))
            fd.write(', \'')
            fd.write(name.replace("'", "\\'"))
            fd.write('\'),\n')
            pbar.update(1)

    fd.seek(fd.tell() - 2)
    fd.write(';\nCOMMIT;\n\n\n')


def write_cantons(fd, cantons):
    """
    Write cantons INSERT INTO statement.
    """
    opening_statement = (
        'SET AUTOCOMMIT=0;\n'
        'INSERT INTO `canton` VALUES\n'
    )

    fd.write(SECTION_HEADER.format(name='canton'))
    fd.write(opening_statement)

    with tqdm(
            total=len(cantons), unit='e', leave=True,
            desc='INSERT INTO canton') as pbar:

        for (province_code, canton_code), name in cantons.items():
            fd.write('(')
            fd.write(str(province_code))
            fd.write('{:02d}'.format(canton_code))
            fd.write(', \'')
            fd.write(name.replace("'", "\\'"))
            fd.write('\', ')
            fd.write(str(province_code))
            fd.write('),\n')
            pbar.update(1)

    fd.seek(fd.tell() - 2)
    fd.write(';\nCOMMIT;\n\n\n')


def write_districts(fd, districts):
    """
    Write districts INSERT INTO statement.
    """
    opening_statement = (
        'SET AUTOCOMMIT=0;\n'
        'INSERT INTO `district` '
        '(`id_district`, `name_district`, `canton_id_canton`) '
        'VALUES\n'
    )
    fd.write(SECTION_HEADER.format(name='district'))
    fd.write(opening_statement)

    with tqdm(
            total=len(districts), unit='e', leave=True,
            desc='INSERT INTO district') as pbar:

        for num, ((province_code, canton_code, district_code), name) \
                in enumerate(districts.items()):

            if num % 1000 == 0 and num > 0:
                fd.seek(fd.tell() - 2)
                fd.write(';\nCOMMIT;\n\n\n')
                fd.write(opening_statement)

            fd.write('(')
            fd.write(str(province_code))
            fd.write('{:02d}'.format(canton_code))
            fd.write('{:03d}'.format(district_code))
            fd.write(', \'')
            fd.write(name.replace("'", "\\'"))
            fd.write('\', ')
            fd.write(str(province_code))
            fd.write('{:02d}'.format(canton_code))
            fd.write('),\n')
            pbar.update(1)

    fd.seek(fd.tell() - 2)
    fd.write(';\nCOMMIT;\n\n\n')


def write_voters(fd, voters):
    """
    Write voters INSERT INTO statement.
    """
    opening_statement = (
        'SET AUTOCOMMIT=0;\n'
        'INSERT INTO `voter` VALUES\n'
    )

    fd.write(SECTION_HEADER.format(name='voter'))
    fd.write(opening_statement)

    with tqdm(
            total=voters.total_voters, unit='v', leave=True,
            unit_scale=True, desc='INSERT INTO voter') as pbar:

        for num, voter in enumerate(voters):

            if num % 1000 == 0 and num > 0:
                fd.seek(fd.tell() - 2)
                fd.write(';\nCOMMIT;\n\n\n')
                fd.write(opening_statement)

            fd.write('(')
            fd.write(str(voter['id'])),
            fd.write(', ')
            fd.write(str(voter['sex'])),
            fd.write(', \'')
            fd.write(voter['expiration'].strftime('%Y-%m-%d')),
            fd.write('\', ')
            fd.write(str(voter['site']))
            fd.write(', \'')
            fd.write(voter['name'].replace("'", "\\'"))
            fd.write('\', \'')
            fd.write(voter['family_name_1'].replace("'", "\\'"))
            fd.write('\', \'')
            fd.write(voter['family_name_2'].replace("'", "\\'"))
            fd.write('\', ')
            fd.write(str(voter['district']))
            fd.write('),\n')
            pbar.update(1)

    fd.seek(fd.tell() - 2)
    fd.write(';\nCOMMIT;\n\n\n')


def write_mysql(fd, payload):
    """
    Write MySQL SQL output.

    :param fd: Output file descriptor.
    :param payload: Generation payload with provinces, cantons, districts and
     voters data.
    """
    fd.write(SCHEMA)
    write_provinces(fd, payload['provinces'])
    write_cantons(fd, payload['cantons'])
    write_districts(fd, payload['districts'])
    write_voters(fd, payload['voters'])
    fd.write(FOOTER)


def write_mysql_scrapper(fd, data):
    """
    Write MySQL SQL output for scrapped data.

    :param fd: Output file descriptor.
    :param dict data: Scrapped data.
    """
    update_statement = (
        'UPDATE `district` SET '
        '`voting_center_name` = \'{}\', '
        '`voting_center_address` = \'{}\', '
        '`voting_center_latitude` = {:9.6f}, '
        '`voting_center_longitude` = {:9.6f} '
        'WHERE `id_district` = {};\n'
    )

    fd.write(SECTION_HEADER.format(name='district'))
    fd.write('USE `tse2sql` ;\n')
    fd.write('SET AUTOCOMMIT=0;\n')

    with tqdm(
            total=len(data), unit='e', leave=True,
            unit_scale=True, desc='UPDATE district') as pbar:

        for district, extras in data.items():
            fd.write(update_statement.format(
                extras['name'].replace("'", "\\'"),
                extras['address'].replace("'", "\\'"),
                extras['latitude'], extras['longitude'],
                district
            ))
            pbar.update(1)

    fd.write('COMMIT;\n')


__all__ = ['write_mysql', 'write_mysql_scrapper']
